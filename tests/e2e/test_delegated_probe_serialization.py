"""Deterministic serialization proof for the qualification cgroup probes.

Issue #73 / ADR-046: `_runtime_v3_verifier_isolation_probe` performs a
drain/enable/restore dance over the shared delegated scope. Unserialized,
a sibling probe observes a transient leaf whose ``cgroup.controllers`` is
still empty and refuses ``E-C18-GATE`` — fail-closed against a healthy
host. These arms prove, without sleep-based flakes:

- the probe must not complete while another process holds the host-probe
  lock (deterministic red on unmodified main: it completes immediately;
  green once the probe acquires the lock itself), and after release it
  restores the caller's cgroup and leaves no ``ranex-*`` leaves;
- two real ``host_confinement qualify`` provisions run concurrently in one
  freshly delegated scope both qualify (the #73 symptom, pinned green).
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
        [
            SYSTEMD_RUN,
            *SCOPE_ARGS,
            "--",
            "cat",
            "/proc/self/cgroup",
        ],
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


LOCK_DRIVER = '''\
import json
import os
import select
import sys
import time
from pathlib import Path

from ranex.cli.host_confinement import (
    _host_probe_lock,
    _move_all_cgroup_processes,
    _runtime_v3_verifier_isolation_probe,
)


def relative_cgroup():
    lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
    unified = [line.split("::", 1)[1] for line in lines if "::" in line]
    assert len(unified) == 1, unified
    return unified[0]


gate_r, gate_w = os.pipe()
done_r, done_w = os.pipe()
initial = relative_cgroup()
root = Path("/sys/fs/cgroup") / initial.lstrip("/")
pid = os.fork()
if pid == 0:
    os.close(gate_w)
    os.close(done_r)
    try:
        os.read(gate_r, 1)
        result = _runtime_v3_verifier_isolation_probe()
        os.write(done_w, b"OK " + json.dumps(result).encode() + b"\\n")
    except BaseException as exc:
        os.write(done_w, b"REFUSED " + repr(exc).encode() + b"\\n")
    finally:
        os._exit(0)
os.close(gate_r)
os.close(done_w)
try:
    with _host_probe_lock():
        # Hold the lock AND the drained topology BEFORE the child starts:
        # every scope member sits in a fresh leaf whose cgroup.controllers
        # is empty, exactly the window a sibling drain opens. An unlocked
        # probe -- or a partial wrap that locks only its mutations while
        # reading controllers outside the lock -- reads this leaf and
        # refuses, so a partial wrap stays red; only acquiring the lock
        # before the first read blocks and waits out the window.
        hold = root / f"ranex-driver-hold-{os.getpid()}"
        hold.mkdir(mode=0o755)
        try:
            _move_all_cgroup_processes(root, hold)
            os.write(gate_w, b"G")
            outcome = None
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline:
                ready, _, _ = select.select([done_r], [], [], 0.2)
                if ready:
                    outcome = os.read(done_r, 1 << 16)
                    break
            if outcome is not None:
                print("UNSERIALIZED " + outcome.decode(), flush=True)
                sys.exit(3)
        finally:
            _move_all_cgroup_processes(hold, root)
            hold.rmdir()
    data = b""
    while not data.endswith(b"\\n"):
        chunk = os.read(done_r, 1 << 16)
        if not chunk:
            break
        data += chunk
finally:
    os.close(gate_w)
    try:
        os.kill(pid, 9)
    except ProcessLookupError:
        pass
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
line = data.decode().strip()
kind, _, payload = line.partition(" ")
if kind != "OK":
    print("REFUSED_AFTER_RELEASE " + payload, flush=True)
    sys.exit(4)
result = json.loads(payload)
expected = {
    "fork",
    "output_write",
    "scratch_write",
    "worker_released",
    "verifier_cgroup_populated_after_drain",
}
assert set(result) == expected, result
assert result["verifier_cgroup_populated_after_drain"] == 0, result
final = relative_cgroup()
root = Path("/sys/fs/cgroup") / final.lstrip("/")
residue = sorted(p.name for p in root.iterdir() if p.name.startswith("ranex-"))
verdict = {
    "initial_relative": initial,
    "final_relative": final,
    "restored": final == initial,
    "residue": residue,
    "probe": result,
}
print("SERIALIZED " + json.dumps(verdict), flush=True)
sys.exit(0 if (verdict["restored"] and not residue) else 5)
'''

PARALLEL_DRIVER = '''\
import json
import subprocess
import sys


def qualify(clone):
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


first, second = qualify(sys.argv[1]), qualify(sys.argv[2])
results = {}
for name, process in (("first", first), ("second", second)):
    out, err = process.communicate(timeout=240)
    results[name] = {
        "exit": process.returncode,
        "stdout_tail": out.strip()[-400:],
        "stderr_tail": err.strip()[-400:],
    }
print("PARALLEL " + json.dumps(results), flush=True)
sys.exit(0 if all(item["exit"] == 0 for item in results.values()) else 6)
'''


def test_v3_verifier_probe_blocks_while_the_host_probe_lock_is_held(tmp_path: Path) -> None:
    driver = tmp_path / "lock-driver.py"
    driver.write_text(LOCK_DRIVER, encoding="utf-8")
    completed = subprocess.run(
        [SYSTEMD_RUN, *SCOPE_ARGS, "--", sys.executable, str(driver)],
        cwd=ROOT,
        env=_child_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    assert "UNSERIALIZED" not in completed.stdout, (
        "the v3 verifier probe completed while the host-probe lock was held — "
        "the probe's cgroup topology dance is not serialized "
        "(issue #73):\n" + completed.stdout
    )
    assert completed.returncode == 0, (
        f"driver exit={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    line = next(item for item in completed.stdout.splitlines() if item.startswith("SERIALIZED "))
    verdict = json.loads(line.removeprefix("SERIALIZED "))
    assert verdict["restored"], verdict
    assert verdict["residue"] == [], verdict
    assert verdict["probe"]["verifier_cgroup_populated_after_drain"] == 0, verdict
    assert "run-" in verdict["final_relative"], verdict


def test_parallel_qualifies_in_one_fresh_delegated_scope_both_qualify(tmp_path: Path) -> None:
    environment = _child_environment()
    clones: list[Path] = []
    for name in ("first", "second"):
        clone = tmp_path / name
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
        clones.append(clone)
    driver = tmp_path / "parallel-driver.py"
    driver.write_text(PARALLEL_DRIVER, encoding="utf-8")
    completed = subprocess.run(
        [SYSTEMD_RUN, *SCOPE_ARGS, "--", sys.executable, str(driver), *clones],
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
    line = next(item for item in completed.stdout.splitlines() if item.startswith("PARALLEL "))
    results = json.loads(line.removeprefix("PARALLEL "))
    for name, item in results.items():
        assert item["exit"] == 0, (name, item)
    for clone in clones:
        report = json.loads(
            (clone / ".local/ranex/qualification/strict-local-v1.json").read_text(encoding="utf-8")
        )
        assert report["qualified"] is True and report["refusal"] is None, report["refusal"]
