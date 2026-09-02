"""Deterministic serialization proof for the strict-local session cgroup path.

Issue #74 / ADR-046 addendum: ``confinement_session`` mutates the shared
delegated-scope topology at two call sites — ``_create_worker_cgroup``
(setup) and ``_release_controller_leaf`` (teardown) — with no lock. A
concurrent qualification probe holding ``_host_probe_lock`` can interleave
with either mutation; either side can then observe a fresh leaf whose
``cgroup.controllers`` is still empty and refuse fail-closed
(E-C18-GATE / E-FACT), the #73 refusal class. These arms prove, without
sleep-based flakes:

- the session's cgroup mutations must not complete while another process
  holds the host-probe lock (deterministic red on unmodified main: a real
  ``host_confinement session`` runs to completion — create AND release —
  under a held lock; green once both session call sites acquire the lock,
  the session then blocks until release and completes green with no
  residue and a restored scope);
- a real session and a real qualify provision run concurrently in one
  freshly delegated scope and both succeed (the steady state the
  serialization buys; pinned green).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
ROOT = E2E_DIR.parents[1]
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

SYSTEMD_RUN = "/usr/bin/systemd-run"
SCOPE_ARGS = (
    "--user",
    "--scope",
    "--quiet",
    "--collect",
    "--same-dir",
    "--property=Delegate=yes",
    "--property=CPUAccounting=yes",
    "--property=MemoryAccounting=yes",
    "--property=TasksAccounting=yes",
)


@pytest.fixture(scope="module", autouse=True)
def _requires_delegated_scope() -> None:
    """This module brings its own fresh delegated scope; can the host make one?"""

    if not Path(SYSTEMD_RUN).is_file():
        pytest.skip("ranex-context:delegated-scope: /usr/bin/systemd-run is absent")
    probe = subprocess.run(
        [SYSTEMD_RUN, *SCOPE_ARGS, "--", "cat", "/proc/self/cgroup"],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    if probe.returncode != 0 or "run-" not in probe.stdout:
        detail = (probe.stderr.strip() or probe.stdout.strip())[:200]
        pytest.skip(f"ranex-context:delegated-scope: a delegated user scope cannot be created here: {detail}")
    controllers = subprocess.run(
        [
            SYSTEMD_RUN,
            *SCOPE_ARGS,
            "--",
            "sh",
            "-c",
            "cat /sys/fs/cgroup$(cat /proc/self/cgroup | sed 's/^0:://')/cgroup.controllers",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    if controllers.returncode != 0 or "pids" not in controllers.stdout.split():
        detail = (controllers.stderr.strip() or controllers.stdout.strip())[:200]
        pytest.skip(
            "ranex-context:delegated-scope: a fresh delegated scope does not "
            f"carry the pids controller here: {detail}"
        )


def _child_environment() -> dict[str, str]:
    base = dict(os.environ)
    entries = [entry for entry in base.get("PYTHONPATH", "").split(os.pathsep) if entry]
    base["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), *entries])
    return _prereqs.wire_child_environment(base)


def _launcher_closure_gate() -> None:
    """The pinned launcher build closure must match this host (a3660edf0's gate)."""

    launcher_host = _prereqs._launcher_host()
    limitation = launcher_host.build_closure_limitation()
    if limitation is not None:
        pytest.skip(
            "ranex-context:host-capability: pinned launcher build closure does "
            f"not match this host — launcher-build refuses E-C17-BUILD-INPUT-DRIFT here ({limitation})"
        )


def _identity_probe(tmp_path: Path) -> Path:
    """One static v1 command allowed by the confined filesystem policy."""

    source = tmp_path / "session-driver-probe.c"
    executable = tmp_path / "session-driver-probe"
    source.write_text(
        """#include <stdio.h>

int main(void) {
    printf("uid-ok\\n");
    return 0;
}
""",
        encoding="utf-8",
    )
    built = subprocess.run(
        [
            "/usr/bin/x86_64-linux-gnu-gcc-13",
            "-std=gnu17",
            "-O2",
            "-static",
            "-fno-pie",
            "-no-pie",
            "-Wl,-z,relro,-z,now",
            "-Wl,-z,noexecstack",
            "-Wl,--build-id=none",
            "-o",
            str(executable),
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    executable.chmod(0o555)
    return executable


SESSION_LOCK_DRIVER = '''\
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

from ranex.cli.host_confinement import _host_probe_lock
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.confinement_result import validate_confinement_result

root = Path(sys.argv[1])
clone = Path(sys.argv[2])
probe = Path(sys.argv[3])

qualify = subprocess.run(
    [
        sys.executable,
        "-m",
        "ranex.cli.host_confinement",
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report",
        ".local/ranex/qualification/strict-local-v1.json",
    ],
    cwd=clone,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    timeout=300,
)
if qualify.returncode != 0:
    print(
        "QUALIFY_REFUSED "
        + json.dumps(
            {
                "exit": qualify.returncode,
                "stdout_tail": qualify.stdout.strip()[-300:],
                "stderr_tail": qualify.stderr.strip()[-300:],
            }
        ),
        flush=True,
    )
    sys.exit(7)


def relative_cgroup():
    lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
    unified = [line.split("::", 1)[1] for line in lines if "::" in line]
    assert len(unified) == 1, unified
    return unified[0]


initial = relative_cgroup()
session_root = clone / ".local" / "ranex-e2e" / "strict-local-v1" / "driver-session"
assert not session_root.exists()
authorities = {name: session_root / name for name in ("subject", "toolchain", "output", "scratch")}
for authority in authorities.values():
    authority.mkdir(parents=True)
descriptor = session_root / "descriptor.json"
result = session_root / "result.json"
descriptor.write_bytes(
    canonical_json_bytes(
        {
            "argv": [str(probe)],
            "environment": {"LC_ALL": "C", "TZ": "UTC"},
            "limits": {
                "cpu_usage_usec": 1_000_000,
                "memory_bytes": 134_217_728,
                "output_bytes": 65_536,
                "output_depth": 8,
                "output_inodes": 32,
                "pids": 16,
                "wall_time_ms": 10_000,
            },
            "output": str(authorities["output"].relative_to(clone)),
            "schema": "ranex-confinement-command-v1",
            "scratch": str(authorities["scratch"].relative_to(clone)),
            "subject": str(authorities["subject"].relative_to(clone)),
            "toolchain": str(authorities["toolchain"].relative_to(clone)),
        }
    )
)
child_env = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "PYTHONPATH": str(clone / "src"),
    "LC_ALL": "C",
    "TZ": "UTC",
}
session_argv = [
    sys.executable,
    "-m",
    "ranex.cli.host_confinement",
    "session",
    "--profile",
    "governance/confinement/strict-local-v1.json",
    "--host-profile",
    "governance/confinement/strict-local-host-v1.json",
    "--artifact",
    ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
    "--manifest",
    "governance/confinement/native-launcher-build-v1.json",
    "--qualification",
    ".local/ranex/qualification/strict-local-v1.json",
    "--descriptor",
    str(descriptor.relative_to(clone)),
    "--result",
    str(result.relative_to(clone)),
]


def spawn_session():
    return subprocess.Popen(
        session_argv,
        cwd=clone,
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


with _host_probe_lock():
    # The lock is held BEFORE the session spawns, so the session's cgroup
    # mutations (worker-cgroup create at setup, controller-leaf release at
    # teardown) cannot precede it. On unmodified main the session runs to
    # completion -- both mutations included -- under the held lock; once
    # both session call sites acquire the lock, the session blocks at the
    # create call and can only complete after this block releases.
    child = spawn_session()
    deadline = time.monotonic() + 30.0
    unserialized = None
    while time.monotonic() < deadline:
        if child.poll() is not None:
            out, err = child.communicate(timeout=30)
            unserialized = {
                "exit": child.returncode,
                "stdout_tail": out.strip()[-300:],
                "stderr_tail": err.strip()[-300:],
            }
            break
        time.sleep(0.2)
    if unserialized is not None:
        print("SESSION_UNSERIALIZED " + json.dumps(unserialized), flush=True)
        sys.exit(3)

out, err = child.communicate(timeout=300)
if child.returncode != 0:
    print(
        "SESSION_REFUSED "
        + json.dumps(
            {
                "exit": child.returncode,
                "stdout_tail": out.strip()[-300:],
                "stderr_tail": err.strip()[-300:],
            }
        ),
        flush=True,
    )
    sys.exit(4)
validated, _digest = validate_confinement_result(result.read_bytes())
command = validated["command"]
assert command["exit_code"] == 0, command
final = relative_cgroup()
scope_root = Path("/sys/fs/cgroup") / final.lstrip("/")
residue = sorted(p.name for p in scope_root.iterdir() if p.name.startswith("ranex-"))
verdict = {
    "initial_relative": initial,
    "final_relative": final,
    "restored": final == initial,
    "residue": residue,
    "session_exit": child.returncode,
    "worker_exit": command["exit_code"],
}
print("SERIALIZED " + json.dumps(verdict), flush=True)
sys.exit(0 if (verdict["restored"] and not residue) else 5)
'''

CONCURRENT_DRIVER = '''\
import json
import os
import subprocess
import sys
from pathlib import Path

clone = Path(sys.argv[1])
probe = Path(sys.argv[2])


def qualify():
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ranex.cli.host_confinement",
            "qualify",
            "--profile",
            "governance/confinement/strict-local-host-v1.json",
            "--artifact",
            ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
            "--manifest",
            "governance/confinement/native-launcher-build-v1.json",
            "--report",
            ".local/ranex/qualification/strict-local-v1.json",
        ],
        cwd=clone,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def session():
    from ranex.foundation.canonical import canonical_json_bytes

    session_root = clone / ".local" / "ranex-e2e" / "strict-local-v1" / "concurrent-session"
    assert not session_root.exists()
    authorities = {name: session_root / name for name in ("subject", "toolchain", "output", "scratch")}
    for authority in authorities.values():
        authority.mkdir(parents=True)
    descriptor = session_root / "descriptor.json"
    result = session_root / "result.json"
    descriptor.write_bytes(
        canonical_json_bytes(
            {
                "argv": [str(probe)],
                "environment": {"LC_ALL": "C", "TZ": "UTC"},
                "limits": {
                    "cpu_usage_usec": 1_000_000,
                    "memory_bytes": 134_217_728,
                    "output_bytes": 65_536,
                    "output_depth": 8,
                    "output_inodes": 32,
                    "pids": 16,
                    "wall_time_ms": 10_000,
                },
                "output": str(authorities["output"].relative_to(clone)),
                "schema": "ranex-confinement-command-v1",
                "scratch": str(authorities["scratch"].relative_to(clone)),
                "subject": str(authorities["subject"].relative_to(clone)),
                "toolchain": str(authorities["toolchain"].relative_to(clone)),
            }
        )
    )
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ranex.cli.host_confinement",
            "session",
            "--profile",
            "governance/confinement/strict-local-v1.json",
            "--host-profile",
            "governance/confinement/strict-local-host-v1.json",
            "--artifact",
            ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
            "--manifest",
            "governance/confinement/native-launcher-build-v1.json",
            "--qualification",
            ".local/ranex/qualification/strict-local-v1.json",
            "--descriptor",
            str(descriptor.relative_to(clone)),
            "--result",
            str(result.relative_to(clone)),
        ],
        cwd=clone,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(clone / "src"),
            "LC_ALL": "C",
            "TZ": "UTC",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


established = subprocess.run(
    [
        sys.executable,
        "-m",
        "ranex.cli.host_confinement",
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report",
        ".local/ranex/qualification/strict-local-v1.json",
    ],
    cwd=clone,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    timeout=300,
)
if established.returncode != 0:
    print(
        "QUALIFY_REFUSED "
        + json.dumps(
            {
                "exit": established.returncode,
                "stdout_tail": established.stdout.strip()[-300:],
                "stderr_tail": established.stderr.strip()[-300:],
            }
        ),
        flush=True,
    )
    sys.exit(7)

first, second = qualify(), session()
results = {}
for name, process in (("qualify", first), ("session", second)):
    out, err = process.communicate(timeout=600)
    results[name] = {
        "exit": process.returncode,
        "stdout_tail": out.strip()[-300:],
        "stderr_tail": err.strip()[-300:],
    }
print("CONCURRENT " + json.dumps(results), flush=True)
sys.exit(0 if all(item["exit"] == 0 for item in results.values()) else 6)
'''


def _prepared_clone(tmp_path: Path, environment: dict[str, str]) -> Path:
    clone = tmp_path / "clone"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(clone)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, cloned.stderr
    for phase in (
        (
            "launcher-build",
            "--manifest",
            "governance/confinement/native-launcher-build-v1.json",
            "--source",
            "native/ranex-worker-launcher/launcher.c",
            "--output",
            ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
        ),
        (
            "launcher-install",
            "--manifest",
            "governance/confinement/native-launcher-build-v1.json",
            "--artifact",
            ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
            "--destination",
            ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        ),
    ):
        built = subprocess.run(
            [sys.executable, "-m", "ranex.cli.host_confinement", *phase],
            cwd=clone,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        assert built.returncode == 0, built.stdout + built.stderr
    return clone


def test_session_cgroup_mutations_block_while_the_host_probe_lock_is_held(
    tmp_path: Path,
) -> None:
    _launcher_closure_gate()
    environment = _child_environment()
    clone = _prepared_clone(tmp_path, environment)
    probe = _identity_probe(tmp_path)
    driver = tmp_path / "session-lock-driver.py"
    driver.write_text(SESSION_LOCK_DRIVER, encoding="utf-8")
    completed = subprocess.run(
        [SYSTEMD_RUN, *SCOPE_ARGS, "--", sys.executable, str(driver), str(ROOT), str(clone), str(probe)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert "SESSION_UNSERIALIZED" not in completed.stdout, (
        "the strict-local session's cgroup mutations completed while the "
        "host-probe lock was held — the session path is not serialized "
        "(issue #74):\n" + completed.stdout
    )
    assert completed.returncode == 0, (
        f"driver exit={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    line = next(item for item in completed.stdout.splitlines() if item.startswith("SERIALIZED "))
    verdict = json.loads(line.removeprefix("SERIALIZED "))
    assert verdict["restored"], verdict
    assert verdict["residue"] == [], verdict
    assert verdict["session_exit"] == 0 and verdict["worker_exit"] == 0, verdict


def test_session_and_qualify_concurrently_in_one_fresh_delegated_scope_both_succeed(
    tmp_path: Path,
) -> None:
    _launcher_closure_gate()
    environment = _child_environment()
    clone = _prepared_clone(tmp_path, environment)
    probe = _identity_probe(tmp_path)
    driver = tmp_path / "session-concurrent-driver.py"
    driver.write_text(CONCURRENT_DRIVER, encoding="utf-8")
    completed = subprocess.run(
        [SYSTEMD_RUN, *SCOPE_ARGS, "--", sys.executable, str(driver), str(clone), str(probe)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert completed.returncode == 0, (
        f"driver exit={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    line = next(item for item in completed.stdout.splitlines() if item.startswith("CONCURRENT "))
    results = json.loads(line.removeprefix("CONCURRENT "))
    for name, item in results.items():
        assert item["exit"] == 0, (name, item)
