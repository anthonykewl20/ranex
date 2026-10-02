"""Install staging must not depend on the operator's umask (#241).

`launcher_install` creates the staging file with `os.open(..., 0o555)` and then
refuses unless the staged mode is exactly 0555. The open mode is masked by the
process umask, so under umask 0077 the file lands at 0500 and install refuses
with E-C17-INSTALL-REFUSED. The fix sets the mode explicitly with
`os.fchmod(staged, 0o555)` before writing, the same pattern the build step
already uses. This suite drives the real `launcher_install` under umask 0077
and asserts the installed launcher keeps mode 0555.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from ranex.cli.host_confinement import (
    BUILD_ARTIFACT_ARGUMENT,
    BUILD_FLAG_PREFIX,
    COMPILER,
    INSTALLED_ARTIFACT_ARGUMENT,
    launcher_install,
)

REPOSITORY = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY / "native/ranex-worker-launcher/launcher.c"

EXPECTED_ELF_FACTS = {
    "bind_now": True,
    "class": "ELF64",
    "endianness": "little",
    "machine": "x86-64",
    "non_executable_stack": True,
    "pie": True,
    "relro": True,
    "type": "DYN",
}


@contextmanager
def _umask(mask: int):
    previous = os.umask(mask)
    try:
        yield
    finally:
        os.umask(previous)


def _compile_launcher(root: Path) -> Path:
    artifact = root / BUILD_ARTIFACT_ARGUMENT
    artifact.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [str(COMPILER), *BUILD_FLAG_PREFIX, "-o", str(artifact), str(SOURCE)],
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    os.chmod(artifact, 0o555)
    return artifact


def _write_manifest(root: Path, artifact: Path) -> str:
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = root / "launcher-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "build": {},
                "source": {},
                "artifact": {"sha256": digest, "elf": EXPECTED_ELF_FACTS},
            }
        ),
        encoding="utf-8",
    )
    return "launcher-manifest.json"


@pytest.mark.skipif(not COMPILER.exists(), reason="launcher compiler unavailable")
def test_launcher_install_staging_mode_is_umask_independent(tmp_path: Path) -> None:
    artifact = _compile_launcher(tmp_path)
    manifest_argument = _write_manifest(tmp_path, artifact)
    installed = tmp_path / INSTALLED_ARTIFACT_ARGUMENT

    with _umask(0o077):
        launcher_install(
            tmp_path, manifest_argument, BUILD_ARTIFACT_ARGUMENT, INSTALLED_ARTIFACT_ARGUMENT
        )

    assert installed.exists()
    assert stat.S_IMODE(installed.stat().st_mode) == 0o555
    # No E-C17-INSTALL-REFUSED escape: reaching this point means install accepted.
    assert not any(
        child.name.startswith(f".{installed.name}.")
        for child in installed.parent.iterdir()
    ), "temporary staging leftovers remain after install"
