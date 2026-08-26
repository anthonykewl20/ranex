"""SLICE-070 real-E2E freeze for the stable strict-local I/O ABI.

The ungated source assertion is honest RED at the absent v2 launcher. A host
which passes the existing qualification fixture then runs the existing public
build/install/qualify/session commands sequentially inside one delegated unit.
The static worker has no repository geometry: it reads ``/ranex/input`` and
creates ``/ranex/output/result.txt``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROFILE = "governance/confinement/strict-local-v2.json"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_OUTPUT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
QUALIFICATION = ".local/ranex/qualification/strict-local-v1.json"
LAUNCHER = ROOT / LAUNCHER_SOURCE
BROKER_PREFIX = [
    "/usr/bin/systemd-run",
    "--user",
    "--no-ask-password",
    "--quiet",
    "--collect",
    "--wait",
    "--pipe",
    "--service-type=exec",
    "--property=Delegate=yes",
    "--property=CPUAccounting=yes",
    "--property=MemoryAccounting=yes",
    "--property=TasksAccounting=yes",
]


def _controller(python: Path, *arguments: str) -> list[str]:
    return [str(python), "-m", "ranex.cli.host_confinement", *arguments]


def _git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def _clean_tracked_tree_fingerprint(checkout: Path) -> str:
    assert _git(checkout, "status", "--porcelain", "--untracked-files=all") == ""
    return _git(checkout, "write-tree").strip()


def test_real_journey_is_wired_to_the_v2_public_surface() -> None:
    """Ungated RED: a profile cannot hide an unimplemented launcher."""

    assert "SYS_open_tree" in LAUNCHER.read_text(encoding="utf-8")
    profile = json.loads((ROOT / PROFILE).read_text(encoding="utf-8"))
    assert profile["cwd"] == "/ranex/input"


@pytest.mark.usefixtures("prereq_qualified_host")
def test_arbitrary_real_code_matches_ordinary_io_and_collected_hashes(
    tmp_path: Path,
) -> None:
    """One delegated identity qualifies and runs through public commands."""

    subject = tmp_path / "subject"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, cloned.stderr

    worker = tmp_path / "slice070-worker"
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
            str(worker),
            str(FIXTURES / "slice070-worker.c"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr

    case = subject / ".local" / "ranex" / "slice070"
    case.mkdir(parents=True)
    input_checkout = case / "input"
    worktree = subprocess.run(
        ["git", "-C", str(subject), "worktree", "add", "--detach", str(input_checkout), "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert worktree.returncode == 0, worktree.stderr
    subject_authority = case / "subject"
    _git(
        subject,
        "worktree",
        "add",
        "--detach",
        str(subject_authority),
        "HEAD",
    )
    paths = {
        name: case / name
        for name in ("toolchain", "output", "scratch")
    }
    ordinary_output = case / "ordinary-output"
    for directory in (*paths.values(), ordinary_output):
        directory.mkdir(parents=True)
    authority_paths = {"input": input_checkout, "subject": subject_authority, **paths}
    resolved_authorities = {
        name: path.resolve(strict=True) for name, path in authority_paths.items()
    }
    authorities = tuple(resolved_authorities.values())
    for index, left in enumerate(authorities):
        for right in authorities[index + 1 :]:
            assert not left.is_relative_to(right)
            assert not right.is_relative_to(left)
    confined_worker = paths["toolchain"] / "bin" / "slice070-worker"
    confined_worker.parent.mkdir()
    confined_worker.write_bytes(worker.read_bytes())
    confined_worker.chmod(0o555)
    subject_anchor = (
        subject_authority
        / "tests"
        / "e2e"
        / "fixtures"
        / "slice070-subject"
        / "anchor.txt"
    )
    anchor_relative = str(subject_anchor.relative_to(subject_authority))
    assert _git(
        subject_authority,
        "ls-files",
        "--error-unmatch",
        "--",
        anchor_relative,
    ).strip() == anchor_relative
    observed_worker = subject_authority / ".local" / "subject-worker"
    observed_worker.parent.mkdir()
    observed_worker.write_bytes(worker.read_bytes())
    observed_worker.chmod(0o555)
    _git(
        subject_authority,
        "check-ignore",
        "--quiet",
        "--",
        str(observed_worker.relative_to(subject_authority)),
    )
    subject_fingerprint = _clean_tracked_tree_fingerprint(subject_authority)

    committed_input = input_checkout / "tests" / "e2e" / "fixtures" / "slice070-input.txt"
    expected = committed_input.read_bytes()
    tracked = subprocess.run(
        [
            "git", "-C", str(input_checkout), "ls-files", "--error-unmatch", "--",
            str(committed_input.relative_to(input_checkout)),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert tracked.returncode == 0, tracked.stderr

    ordinary_input = case / "ordinary-input.txt"
    ordinary_input.write_bytes(expected)
    ordinary_input.chmod(0o444)
    ordinary_result = ordinary_output / "result.txt"
    ordinary = subprocess.run(
        [
            str(worker),
            "--require-input-read-only",
            str(ordinary_input),
            str(ordinary_result),
        ],
        cwd=subject,
        env={"LC_ALL": "C", "TZ": "UTC"},
        capture_output=True,
        check=False,
    )
    assert ordinary.returncode == 0, ordinary.stderr

    descriptor = {
        "argv": [
            "/ranex/toolchain/bin/slice070-worker",
            "--require-authority-read-only",
            "/ranex/input/tests/e2e/fixtures/slice070-input.txt",
            "/ranex/toolchain/bin/slice070-worker",
            "/ranex/output/result.txt",
        ],
        "environment": {"LC_ALL": "C", "TZ": "UTC"},
        "limits": {
            "cpu_usage_usec": 1_000_000,
            "memory_bytes": 134_217_728,
            "output_bytes": 65_536,
            "output_depth": 8,
            "output_inodes": 32,
            "pids": 16,
            "wall_time_ms": 5_000,
        },
        "input": str(input_checkout.relative_to(subject)),
        "output": str(paths["output"].relative_to(subject)),
        "schema": "ranex-confinement-command-v1",
        "scratch": str(paths["scratch"].relative_to(subject)),
        "subject": str(subject_authority.relative_to(subject)),
        "toolchain": str(paths["toolchain"].relative_to(subject)),
    }
    descriptor_path = case / "descriptor.json"
    result_path = case / "result.json"
    descriptor_path.write_bytes(canonical_json_bytes(descriptor))
    subject_exec_descriptor = {
        **descriptor,
        "argv": [
            "/ranex/subject/.local/subject-worker",
            "--require-input-read-only",
            "/ranex/input/tests/e2e/fixtures/slice070-input.txt",
            "/ranex/output/subject-exec-must-not-exist.txt",
        ],
    }
    subject_exec_descriptor_path = case / "subject-exec-descriptor.json"
    subject_exec_result_path = case / "subject-exec-result.json"
    subject_exec_descriptor_path.write_bytes(canonical_json_bytes(subject_exec_descriptor))

    development_python = Path(sys.executable).resolve()
    steps = [
        _controller(
            development_python, "launcher-build", "--manifest", MANIFEST,
            "--source", LAUNCHER_SOURCE, "--output", BUILD_OUTPUT,
        ),
        _controller(
            development_python, "launcher-install", "--manifest", MANIFEST,
            "--artifact", BUILD_OUTPUT, "--destination", INSTALLED_LAUNCHER,
        ),
        _controller(
            development_python, "qualify", "--profile", HOST_PROFILE,
            "--artifact", INSTALLED_LAUNCHER, "--manifest", MANIFEST,
            "--report", QUALIFICATION,
        ),
        _controller(
            development_python, "session", "--profile", PROFILE,
            "--host-profile", HOST_PROFILE, "--artifact", INSTALLED_LAUNCHER,
            "--manifest", MANIFEST, "--qualification", QUALIFICATION,
            "--descriptor", str(descriptor_path.relative_to(subject)),
            "--result", str(result_path.relative_to(subject)),
        ),
        _controller(
            development_python, "session", "--profile", PROFILE,
            "--host-profile", HOST_PROFILE, "--artifact", INSTALLED_LAUNCHER,
            "--manifest", MANIFEST, "--qualification", QUALIFICATION,
            "--descriptor", str(subject_exec_descriptor_path.relative_to(subject)),
            "--result", str(subject_exec_result_path.relative_to(subject)),
        ),
    ]
    shell_program = "set -eu; " + "; ".join(shlex.join(step) for step in steps)
    completed = subprocess.run(
        [
            *BROKER_PREFIX,
            f"--working-directory={subject}",
            f"--setenv=PYTHONPATH={subject / 'src'}",
            "--setenv=PATH=/usr/bin:/bin",
            "--setenv=LC_ALL=C",
            "--setenv=TZ=UTC",
            "/bin/sh", "-c", shell_program,
        ],
        cwd=subject,
        env={
            name: value
            for name, value in os.environ.items()
            if name != "RANEX_SIGNING_KEY"
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert _clean_tracked_tree_fingerprint(subject_authority) == subject_fingerprint

    subject_exec_result = json.loads(
        subject_exec_result_path.read_text(encoding="utf-8")
    )
    assert subject_exec_result["command"]["exit_code"] != 0
    assert subject_exec_result["outputs"] == {"bytes": 0, "files": [], "inodes": 0}
    assert not (paths["output"] / "subject-exec-must-not-exist.txt").exists()

    result = json.loads(result_path.read_text(encoding="utf-8"))
    confined_result = paths["output"] / "result.txt"
    assert result["command"]["exit_code"] == ordinary.returncode == 0
    assert confined_result.read_bytes() == ordinary_result.read_bytes() == expected
    digest = hashlib.sha256(expected).hexdigest()
    assert result["outputs"] == {
        "bytes": len(expected),
        "files": [{"bytes": len(expected), "path": "result.txt", "sha256": digest}],
        "inodes": 1,
    }
    assert set(result["profile_digests"]) == {"host", "launcher", "runtime"}
    assert all(
        isinstance(value, str) and len(value) == 64
        for value in result["profile_digests"].values()
    )
