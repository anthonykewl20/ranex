"""Produce host evidence through the shipped controller and signing CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import _prereqs


def record_host_qualification(repo: Path, key_path: Path, *, producer_id: str = "worker") -> None:
    _prereqs.prereq_or_skip("qualified_host")
    profile = "governance/confinement/strict-local-host-v1.json"
    manifest = "governance/confinement/native-launcher-build-v1.json"
    source = "native/ranex-worker-launcher/launcher.c"
    build = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
    artifact = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
    environment = {**os.environ, "PYTHONPATH": str(repo / "src")}
    environment.pop("RANEX_SIGNING_KEY", None)
    commands = (
        ["ranex.cli.host_confinement", "launcher-build", "--manifest", manifest,
         "--source", source, "--output", build],
        ["ranex.cli.host_confinement", "launcher-install", "--manifest", manifest,
         "--artifact", build, "--destination", artifact],
        ["ranex.cli.main", "run", "--claim", "host-qualification", "--producer", producer_id,
         "--", "python", "-m", "ranex.cli.host_confinement", "qualify", "--profile", profile,
         "--artifact", artifact, "--manifest", manifest,
         "--report=.local/ranex/qualification/strict-local-v1.json"],
    )
    for command in commands:
        scoped = dict(environment)
        if command[0] == "ranex.cli.main":
            scoped["RANEX_SIGNING_KEY"] = str(key_path)
        completed = subprocess.run([sys.executable, "-m", *command], cwd=repo, env=scoped,
                                   capture_output=True, text=True, check=False, timeout=240)
        assert completed.returncode == 0, (
            f"real host qualification command failed: {command!r}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
