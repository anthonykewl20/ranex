"""Operator-facing workflow around the strict-local confinement kernel.

The user scope re-exec inherits operator environment such as ``RANEX_SIGNING_KEY``;
secrets are never written into systemd unit properties or argv.

Usage: ``ranex host strict-local --version VERSION --claim CLAIM --producer PRODUCER
[run metadata] -- COMMAND``.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, NoReturn

from ranex.execution.log_redaction import collect_redaction_literals
from ranex.execution.retained_logs import (
    DEFAULT_LOG_MAX_BYTES,
    persist_stream,
    write_log_manifest,
)
from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes

BUILD_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
BUILD_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_ARTIFACT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_ARTIFACT = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
QUALIFICATION_REPORT = ".local/ranex/qualification/strict-local-v1.json"

# SLICE-047 permits only the confinement module to import itself. These copied
# public protocol literals allow this operator wrapper to invoke it as a child,
# rather than importing the confinement kernel into the parent process.
E_EXEC = "E-C17-EXEC-OBJECT-DRIFT"
E_C18_GATE = "E-C18-GATE"
E_C18_READBACK = "E-C18-CGROUP-READBACK"
E_C18_LIMIT = "E-C18-LIMIT"
E_C18_DRAIN = "E-C18-DRAIN"
E_C18_OUTPUT_UNSAFE = "E-C18-OUTPUT-UNSAFE"
E_C18_OUTPUT_BOUND = "E-C18-OUTPUT-BOUND"
E_C18_OUTPUT_RACE = "E-C18-OUTPUT-RACE"
E_C18_RESULT = "E-C18-RESULT"
E_C18_PATH_ALIAS = "E-C18-PATH-ALIAS"
E_C18_HOST_DRIFT = "E-C18-HOST-DRIFT"
REQUIRED_CONTROLLERS = frozenset({"cpu", "memory", "pids"})

# Keep this ordered catalogue closed to the confinement protocol's C18 names
# so a new kernel refusal cannot silently lack an operator remedy.
PREFLIGHT_CHECKS = (
    E_C18_GATE,
    E_C18_READBACK,
    E_C18_LIMIT,
    E_C18_DRAIN,
    E_C18_OUTPUT_UNSAFE,
    E_C18_OUTPUT_BOUND,
    E_C18_OUTPUT_RACE,
    E_C18_RESULT,
    E_C18_PATH_ALIAS,
    E_C18_HOST_DRIFT,
)
_PREFLIGHT_NAMES = (
    "pid1-systemd",
    "systemd-run-present",
    "user-session-bus",
    "user-manager-alive",
    "not-root",
    "build-closure",
    "already-delegated",
)

CORRECTIVE_ACTIONS: dict[str, str] = {
    E_C18_GATE: "gate admission failed; restore the pinned governed inputs and retry.",
    E_C18_READBACK: "cgroup readback failed; inspect delegated controller state and retry.",
    E_C18_LIMIT: "a confinement limit was not applied; repair the host systemd policy.",
    E_C18_DRAIN: "cgroup drain failed; stop remaining workload processes before retrying.",
    E_C18_OUTPUT_UNSAFE: "output safety check failed; use a fresh admitted result directory.",
    E_C18_OUTPUT_BOUND: "output bounds check failed; reduce the output to its configured limit.",
    E_C18_OUTPUT_RACE: "output changed during collection; retry with an exclusively owned directory.",
    E_C18_RESULT: "result validation failed; remove the invalid result and rerun qualification.",
    E_C18_PATH_ALIAS: "path aliasing was detected; provide canonical repository-relative paths.",
    E_C18_HOST_DRIFT: "host facts drifted; requalify this host before running strict-local work.",
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    corrective_action: str


@dataclass(frozen=True)
class StepResult:
    name: str
    argv: list[str]
    exit_code: int
    refusal_code: str | None
    refusal_detail: str | None
    stdout: str
    stderr: str


def corrective_for(code: str) -> str:
    """Return the durable corrective instruction for a kernel refusal."""
    if code == E_EXEC:
        return "the executable object drifted; rebuild the admitted launcher and requalify the host."
    return CORRECTIVE_ACTIONS.get(code, "inspect the failed host check, correct it, and retry the operation.")


def _check(name: str, ok: bool, detail: str) -> CheckResult:
    return CheckResult(
        name,
        ok,
        detail,
        f"{name} failed; correct the host prerequisite and retry strict-local delegation.",
    )


def delegated_controllers() -> tuple[Path, str, frozenset[str]]:
    """Read the current unified cgroup and its available controllers."""
    lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
    unified = [line.split("::", 1)[1] for line in lines if "::" in line]
    if len(unified) != 1 or not unified[0].startswith("/"):
        raise ValueError("cannot resolve the unified cgroup from /proc/self/cgroup")
    relative = unified[0]
    root = Path("/sys/fs/cgroup") / relative.lstrip("/")
    controllers = frozenset((root / "cgroup.controllers").read_text().split())
    return root, relative, controllers


def preflight_checks(*, build_needed: bool) -> list[CheckResult]:
    """Perform the host-only checks needed before entering a delegated scope."""
    pid1 = Path("/proc/1/comm")
    try:
        pid1_comm = pid1.read_text(encoding="utf-8").strip()
    except OSError as exc:
        pid1_comm = ""
        pid1_detail = f"cannot read /proc/1/comm: {exc}"
    else:
        pid1_detail = f"pid 1 is {pid1_comm!r}"
    checks = [_check(_PREFLIGHT_NAMES[0], pid1_comm == "systemd", pid1_detail)]
    systemd_run = Path("/usr/bin/systemd-run")
    checks.append(_check(_PREFLIGHT_NAMES[1], systemd_run.is_file() and os.access(systemd_run, os.X_OK), "requires executable /usr/bin/systemd-run"))
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    bus = Path(runtime) / "bus" if runtime else None
    session_bus = bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS")) or bool(bus and bus.is_socket())
    checks.append(_check(_PREFLIGHT_NAMES[2], session_bus, "requires XDG runtime bus or DBUS session bus"))
    try:
        manager = subprocess.run(
            ["/usr/bin/systemctl", "--user", "is-system-running"],
            capture_output=True,
            check=False,
            text=True,
        ).stdout.strip()
    except OSError as exc:
        manager = ""
        manager_detail = f"cannot query user manager: {exc}"
    else:
        manager_detail = "desktop-unit failures do not block delegation" if manager == "degraded" else f"user manager is {manager!r}"
    checks.append(_check(_PREFLIGHT_NAMES[3], manager in {"running", "degraded"}, manager_detail))
    checks.append(_check(_PREFLIGHT_NAMES[4], os.geteuid() != 0, "strict-local must run as an unprivileged user"))
    closure_ok = True
    closure_detail = "build closure already available"
    if build_needed:
        compiler = Path("/usr/bin/x86_64-linux-gnu-gcc-13")
        closure_ok = compiler.is_file() and os.access(compiler, os.X_OK) and Path(BUILD_MANIFEST).is_file()
        closure_detail = "requires gcc-13 and the committed launcher build manifest"
    checks.append(_check(_PREFLIGHT_NAMES[5], closure_ok, closure_detail))
    try:
        _root, _relative, controllers = delegated_controllers()
        delegated = REQUIRED_CONTROLLERS <= controllers
        delegation_detail = f"available controllers: {', '.join(sorted(controllers))}"
    except (OSError, ValueError) as exc:
        delegated = False
        delegation_detail = f"cannot inspect current cgroup delegation: {exc}"
    checks.append(_check(_PREFLIGHT_NAMES[6], delegated, delegation_detail))
    return checks


def enter_delegated_scope(argv: Sequence[str]) -> NoReturn:
    """Re-exec this command in an accounting-enabled user scope."""
    scope_argv = [
        "/usr/bin/systemd-run", "--user", "--scope", "--quiet", "--collect", "--same-dir",
        "--property=Delegate=yes", "--property=CPUAccounting=yes", "--property=MemoryAccounting=yes",
        "--property=TasksAccounting=yes", "--setenv=RANEX_STRICT_LOCAL_IN_SCOPE=1", "--", *argv,
    ]
    environment = dict(os.environ)
    environment["RANEX_STRICT_LOCAL_IN_SCOPE"] = "1"
    os.execve(scope_argv[0], scope_argv, environment)
    raise AssertionError("os.execve returned")


def _run_step(name: str, argv: Sequence[str]) -> StepResult:
    """Run one kernel operation and decode its canonical refusal, if any."""
    completed = subprocess.run(list(argv), capture_output=True, check=False, text=True)
    code, detail = _refusal_from_streams(completed.stdout, completed.stderr)
    return StepResult(name, list(argv), completed.returncode, code, detail, completed.stdout, completed.stderr)


def _confinement_argv(argv: Sequence[str]) -> list[str]:
    """Build the module-child invocation for one confinement operation."""
    return ["python", "-m", "ranex.cli.host_confinement", *argv]


_ERROR_REFUSAL = re.compile(r"^ERROR\s+(E-C1[78][A-Z0-9-]*):\s*(.+)$", re.MULTILINE)


def _refusal_from_streams(stdout: str, stderr: str) -> tuple[str | None, str | None]:
    """Decode either the kernel JSON record or ``ranex run``'s stderr error."""
    for stream in (stdout, stderr):
        try:
            value = json.loads(stream)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            code = value.get("refusal")
            detail = value.get("detail")
            if isinstance(code, str) and isinstance(detail, str):
                return code, detail
    match = _ERROR_REFUSAL.search(stderr)
    if match is not None:
        return match.group(1), match.group(2)
    return None, None


def launcher_identity(artifact: Path, manifest: Path) -> dict[str, object]:
    """Return the on-disk identity of the launcher and its build manifest."""
    def digest(path: Path) -> str | None:
        try:
            return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None
    artifact_digest, manifest_digest = digest(artifact), digest(manifest)
    try:
        pinned = json.loads(manifest.read_text(encoding="utf-8"))["artifact"]["sha256"]
    except (OSError, TypeError, KeyError, json.JSONDecodeError):
        pinned = None
    matches = isinstance(pinned, str) and artifact_digest == f"sha256:{pinned}"
    return {"protocol": "ranex-launcher-v1", "artifact": str(artifact), "artifact_sha256": artifact_digest, "manifest": str(manifest), "manifest_sha256": manifest_digest, "matches": matches}


def _launcher_matches_manifest(artifact: Path, manifest: Path) -> bool:
    """Check the build manifest's admitted launcher digest without rebuilding."""
    try:
        expected = json.loads(manifest.read_text(encoding="utf-8"))["artifact"]["sha256"]
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
    except (OSError, TypeError, KeyError, json.JSONDecodeError):
        return False
    return isinstance(expected, str) and expected == actual


def _managed_launcher_is_unchanged() -> bool:
    """Only skip install when the workflow's fixed libexec file is identical."""
    artifact = Path(BUILD_ARTIFACT)
    destination = Path(INSTALLED_ARTIFACT)
    try:
        return hashlib.sha256(artifact.read_bytes()).digest() == hashlib.sha256(
            destination.read_bytes()
        ).digest()
    except OSError:
        return False


def _host_facts() -> dict[str, object]:
    def text(path: str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except OSError:
            return None
    try:
        is_system_running = subprocess.run(
            ["/usr/bin/systemctl", "--user", "is-system-running"],
            capture_output=True,
            check=False,
            text=True,
        ).stdout.strip()
    except OSError:
        is_system_running = None
    return {"uname": platform.uname()._asdict(), "boot_id": text("/proc/sys/kernel/random/boot_id"), "machine_id": text("/etc/machine-id"), "pid1_comm": text("/proc/1/comm"), "is_system_running": is_system_running}


def write_run_report(result_dir: Path, report: dict[str, object]) -> Path:
    """Persist redacted logs and the closed canonical run-report envelope."""
    result_dir = result_dir.absolute()
    logs_dir = result_dir / "logs"
    literals = collect_redaction_literals(os.environ)
    streams = {
        "stdout": persist_stream(logs_dir, "stdout", str(report.pop("_stdout", "")), literals=literals, max_bytes=DEFAULT_LOG_MAX_BYTES),
        "stderr": persist_stream(logs_dir, "stderr", str(report.pop("_stderr", "")), literals=literals, max_bytes=DEFAULT_LOG_MAX_BYTES),
    }
    write_log_manifest(logs_dir, streams, {"max_bytes": DEFAULT_LOG_MAX_BYTES})
    report["logs"] = {name: {key: value[key] for key in ("file", "bytes", "sha256")} for name, value in streams.items()}
    qualification = report.get("qualification")
    if isinstance(qualification, dict) and isinstance(qualification.get("path"), str):
        source = Path(qualification["path"])
        try:
            write_atomic(result_dir / "qualification.json", source.read_bytes(), root=result_dir)
        except OSError:
            pass
    path = result_dir / "host-run-report.json"
    write_atomic(path, canonical_json_bytes(report) + b"\n", root=result_dir)
    return path


def _operator_report(result_dir: Path, *, outcome: str, step: StepResult, scope: dict[str, object] | None = None) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report: dict[str, object] = {"schema": "ranex-host-strict-local-run-v1", "started_at": now, "finished_at": now, "outcome": outcome, "host": _host_facts(), "scope": scope or {"entered": False, "method": "none", "cgroup_root": None, "cgroup_relative_path": None, "controllers": []}, "checks": [], "steps": [asdict(step)], "launcher": launcher_identity(Path(BUILD_ARTIFACT), Path(BUILD_MANIFEST)), "qualification": {"path": QUALIFICATION_REPORT}, "command": {"argv": [], "exit_code": step.exit_code}, "result_binding": None, "logs": {}, "_stdout": step.stdout, "_stderr": step.stderr}
    write_run_report(result_dir, report)


def run_operator(args: Any, argv: list[str], lifecycle: str, artifact: str) -> int:
    """Forward a single host verb while retaining its operator report."""
    step = _run_step(argv[0], _confinement_argv(argv))
    _operator_report(
        Path(args.result_dir),
        outcome="confined" if step.exit_code == 0 else "refused",
        step=step,
    )
    if step.exit_code == 0:
        print(f"{lifecycle}  {artifact}")
    elif step.refusal_code is not None and step.refusal_detail is not None:
        print(f"ERROR  {step.refusal_code}: {step.refusal_detail}", file=os.sys.stderr)
        print(f"HINT  {corrective_for(step.refusal_code)}", file=os.sys.stderr)
    return step.exit_code


def _validate_pairing(version: str, runtime: str | None, toolchain: str | None, closure: str | None) -> str | None:
    if version == "v2" and (not runtime or not toolchain or closure):
        return "v2 requires --runtime-input-path and --toolchain-root, and excludes --runtime-closure-root"
    if version == "v3" and (not runtime or not closure or toolchain):
        return "v3 requires --runtime-input-path and --runtime-closure-root, and excludes --toolchain-root"
    return None


def _run_metadata_argv(
    *,
    claim: str | None,
    producer: str | None,
    repository: str | None,
    evidence: str | None,
    producers: str | None,
    gate: str | None,
    gate_catalog: str | None,
    suite_manifest: str | None,
    store: str | None,
) -> list[str]:
    """Build the optional run metadata prefix in its public flag order."""
    values = (
        ("--claim", claim),
        ("--producer", producer),
        ("--repository", repository),
        ("--evidence", evidence),
        ("--producers", producers),
        ("--gate", gate),
        ("--gate-catalog", gate_catalog),
        ("--suite-manifest", suite_manifest),
        ("--store", store),
    )
    return [item for flag, value in values if value is not None for item in (flag, value)]


def run_workflow(
    version: str,
    *,
    runtime_input_path: str | None,
    toolchain_root: str | None,
    runtime_closure_root: str | None,
    command: Sequence[str],
    result_dir: str,
    skip_build: bool,
    claim: str | None = None,
    producer: str | None = None,
    repository: str | None = None,
    evidence: str | None = None,
    producers: str | None = None,
    gate: str | None = None,
    gate_catalog: str | None = None,
    suite_manifest: str | None = None,
    store: str | None = None,
) -> int:
    """Run build, install, qualification, then the strict-local command."""
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    steps: list[StepResult] = []
    empty_scope: dict[str, object] = {
        "entered": False,
        "method": "none",
        "cgroup_root": None,
        "cgroup_relative_path": None,
        "controllers": [],
    }

    def finish(
        outcome: str,
        exit_code: int | None,
        checks: Sequence[CheckResult] = (),
        scope: dict[str, object] | None = None,
    ) -> int:
        report: dict[str, object] = {
            "schema": "ranex-host-strict-local-run-v1",
            "started_at": started,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "outcome": outcome,
            "host": _host_facts(),
            "scope": scope or empty_scope,
            "checks": [asdict(check) for check in checks],
            "steps": [asdict(step) for step in steps],
            "launcher": launcher_identity(Path(BUILD_ARTIFACT), Path(BUILD_MANIFEST)),
            "qualification": {"path": QUALIFICATION_REPORT},
            "command": {"argv": list(command), "exit_code": exit_code},
            "result_binding": None,
            "logs": {},
            "_stdout": "".join(step.stdout for step in steps),
            "_stderr": "".join(step.stderr for step in steps),
        }
        write_run_report(Path(result_dir), report)
        return 2 if exit_code is None else exit_code

    pairing = _validate_pairing(version, runtime_input_path, toolchain_root, runtime_closure_root)
    if pairing is not None:
        print(f"ERROR  {pairing}", file=os.sys.stderr)
        return finish("prereq-failed", 2)
    launcher_matches = _launcher_matches_manifest(Path(BUILD_ARTIFACT), Path(BUILD_MANIFEST))
    checks = preflight_checks(build_needed=not skip_build or not launcher_matches)
    try:
        root, relative, controllers = delegated_controllers()
    except (OSError, ValueError):
        root, relative, controllers = Path("/sys/fs/cgroup"), "/", frozenset()
    scope: dict[str, object] = {
        "entered": os.environ.get("RANEX_STRICT_LOCAL_IN_SCOPE") == "1",
        "method": "in-place" if REQUIRED_CONTROLLERS <= controllers else "systemd-run",
        "cgroup_root": str(root),
        "cgroup_relative_path": relative,
        "controllers": sorted(controllers),
    }
    failed = next((check for check in checks if not check.ok and check.name != "already-delegated"), None)
    if failed is not None:
        print(f"ERROR  {failed.name}: {failed.detail}", file=os.sys.stderr)
        print(f"HINT  {failed.corrective_action}", file=os.sys.stderr)
        return finish("prereq-failed", 1, checks, scope)
    metadata_argv = _run_metadata_argv(
        claim=claim,
        producer=producer,
        repository=repository,
        evidence=evidence,
        producers=producers,
        gate=gate,
        gate_catalog=gate_catalog,
        suite_manifest=suite_manifest,
        store=store,
    )
    if not scope["entered"] and scope["method"] == "systemd-run":
        print("ENTERED  strict-local delegated scope")
        scope_argv = [
            "ranex",
            "host",
            "strict-local",
            "--version",
            version,
            "--result-dir",
            result_dir,
        ]
        scope_argv.extend(metadata_argv)
        if runtime_input_path is not None:
            scope_argv.extend(["--runtime-input-path", runtime_input_path])
        if toolchain_root is not None:
            scope_argv.extend(["--toolchain-root", toolchain_root])
        if runtime_closure_root is not None:
            scope_argv.extend(["--runtime-closure-root", runtime_closure_root])
        if skip_build:
            scope_argv.append("--skip-build")
        scope_argv.extend(["--", *command])
        enter_delegated_scope(scope_argv)
    phase_argvs: list[tuple[str, list[str], str, str, bool]] = []
    if not (skip_build and launcher_matches):
        phase_argvs.append(("launcher-build", ["python", "-m", "ranex.cli.host_confinement", "launcher-build", "--manifest", BUILD_MANIFEST, "--source", BUILD_SOURCE, "--output", BUILD_ARTIFACT], "BUILT", BUILD_ARTIFACT, False))
    install_argv = ["python", "-m", "ranex.cli.host_confinement", "launcher-install", "--manifest", BUILD_MANIFEST, "--artifact", BUILD_ARTIFACT, "--destination", INSTALLED_ARTIFACT]
    install_unchanged = _managed_launcher_is_unchanged()
    phase_argvs.append(("launcher-install", install_argv, "INSTALLED", INSTALLED_ARTIFACT, install_unchanged))
    phase_argvs.append(("qualify", ["python", "-m", "ranex.cli.host_confinement", "qualify", "--profile", HOST_PROFILE, "--artifact", INSTALLED_ARTIFACT, "--manifest", BUILD_MANIFEST, "--report", QUALIFICATION_REPORT], "QUALIFIED", QUALIFICATION_REPORT, False))
    for name, argv, line, artifact, unchanged in phase_argvs:
        step = StepResult(name, argv, 0, None, None, "", "") if unchanged else _run_step(name, argv)
        steps.append(step)
        if step.exit_code != 0:
            if step.refusal_code and step.refusal_detail:
                print(f"ERROR  {step.refusal_code}: {step.refusal_detail}", file=os.sys.stderr)
                print(f"HINT  {corrective_for(step.refusal_code)}", file=os.sys.stderr)
            return finish("refused", step.exit_code, checks, scope)
        if unchanged:
            print(f"INSTALLED  launcher={INSTALLED_ARTIFACT} (unchanged)")
        else:
            print(f"{line}  {artifact}")
    run_argv = ["ranex", "run", *metadata_argv, "--confinement", "strict-local"]
    if runtime_input_path:
        run_argv.extend(["--runtime-input-path", runtime_input_path])
    if toolchain_root:
        run_argv.extend(["--toolchain-root", toolchain_root])
    if runtime_closure_root:
        run_argv.extend(["--runtime-closure-root", runtime_closure_root])
    run_argv.extend(["--", *command])
    step = _run_step("run", run_argv)
    steps.append(step)
    if step.exit_code == 0:
        print("CONFINED  strict-local command")
    elif step.refusal_code is not None and step.refusal_detail is not None:
        print(f"ERROR  {step.refusal_code}: {step.refusal_detail}", file=os.sys.stderr)
        print(f"HINT  {corrective_for(step.refusal_code)}", file=os.sys.stderr)
    return finish("confined" if step.exit_code == 0 else "refused", step.exit_code, checks, scope)


def main(args: Any) -> int:
    """Dispatch the ``ranex host`` argparse namespace."""
    action = args.action
    if action == "launcher-build":
        return run_operator(args, [action, "--manifest", args.manifest, "--source", args.source, "--output", args.output], "BUILT", args.output)
    if action == "launcher-install":
        return run_operator(args, [action, "--manifest", args.manifest, "--artifact", args.artifact, "--destination", args.destination], "INSTALLED", args.destination)
    if action == "host-probe":
        return run_operator(args, [action], "PROBED", "host facts")
    if action == "qualify":
        return run_operator(args, [action, "--profile", args.profile, "--artifact", args.artifact, "--manifest", args.manifest, "--report", args.report], "QUALIFIED", args.report)
    if action == "launcher-identity":
        print(canonical_json_bytes(launcher_identity(Path(args.artifact), Path(args.manifest))).decode())
        return 0
    return run_workflow(
        args.version,
        runtime_input_path=args.runtime_input_path,
        toolchain_root=args.toolchain_root,
        runtime_closure_root=args.runtime_closure_root,
        command=args.command[1:] if args.command[:1] == ["--"] else args.command,
        result_dir=args.result_dir,
        skip_build=args.skip_build,
        claim=args.claim,
        producer=args.producer,
        repository=args.repository,
        evidence=args.evidence,
        producers=args.producers,
        gate=args.gate,
        gate_catalog=args.gate_catalog,
        suite_manifest=args.suite_manifest,
        store=args.store,
    )
