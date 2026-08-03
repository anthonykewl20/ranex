"""Assemble a disposable, sealed environment from verified store entries.

The root is rebuilt for every run inside the run's own scratch, from store
bytes that were re-hashed on the way out, and sealed read-only before the
command spawns. Nothing durable depends on it: a command that defeats the
seal has changed a directory that is about to be deleted, while the store
it was built from re-verifies on every later read. That is the honest scope
of ADR-007 sad path 13 without ADR-006's confinement — deny the plain
write, and make the target worthless to corrupt.
"""

from __future__ import annotations

import os
import stat
import subprocess
from collections.abc import Sequence
from pathlib import Path

from ranex.cli.toolchain import pinned_path_value
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.lockfile import WheelArtifact
from ranex.provisioning.pins import ResolutionPins
from ranex.provisioning.store import StoreError, WheelStore


class RootError(ProvisioningError):
    """The dependency root cannot be assembled from verified entries."""


def verified_wheel_paths(
    artifacts: Sequence[WheelArtifact], store: WheelStore
) -> tuple[Path, ...]:
    """Every selected wheel, re-verified, with the missing one named."""

    paths: list[Path] = []
    for artifact in artifacts:
        try:
            paths.append(store.verified_path(artifact.sha256))
        except StoreError as exc:
            raise RootError(
                f"wheel for {artifact.package} {artifact.version} is not "
                f"available from the store: {exc}. Only `ranex deps fetch` "
                "may bring it in; the gated run never reaches the network"
            ) from exc
    return tuple(paths)


def _seal(root: Path) -> None:
    """Remove every write bit underneath ``root``, directories included."""

    for parent, directories, files in os.walk(root, topdown=False):
        for name in (*directories, *files):
            path = Path(parent, name)
            if path.is_symlink():
                continue
            mode = stat.S_IMODE(path.lstat().st_mode)
            path.chmod(mode & ~0o222)
    root.chmod(stat.S_IMODE(root.lstat().st_mode) & ~0o222)


def assemble_root(
    artifacts: Sequence[WheelArtifact],
    store: WheelStore,
    pins: ResolutionPins,
    resolver_descriptor: int,
    destination: Path,
) -> Path:
    """Build and seal the environment; return the environment directory.

    The installer is the pinned resolver through its verified descriptor, and
    it installs exact files with `--no-deps`: resolution already happened in
    the lock, so nothing here may choose, substitute or complete the set.
    """

    links = destination / "wheels"
    environment = destination / "env"
    scratch_home = destination / "home"
    cache = destination / "cache"
    for directory in (links, scratch_home, cache):
        directory.mkdir(parents=True, exist_ok=True)

    named: list[Path] = []
    for artifact, source in zip(
        artifacts, verified_wheel_paths(artifacts, store), strict=True
    ):
        # The installer parses tags from the filename, so the store entry is
        # linked under the name the lock's url carries. A hard link shares the
        # verified bytes; a filesystem that refuses one gets a copy.
        target = links / artifact.filename
        try:
            os.link(source, target)
        except OSError:
            target.write_bytes(source.read_bytes())
        named.append(target)

    environment_variables = {
        "PATH": pinned_path_value(),
        "HOME": str(scratch_home),
        "UV_NO_CONFIG": "1",
        "UV_CACHE_DIR": str(cache),
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_OFFLINE": "1",
    }

    def resolver(arguments: list[str], failure: str) -> None:
        try:
            completed = subprocess.run(
                ["uv", *arguments],
                executable=f"/proc/self/fd/{resolver_descriptor}",
                pass_fds=(resolver_descriptor,),
                capture_output=True,
                text=True,
                check=False,
                env=environment_variables,
            )
        except OSError as exc:
            raise RootError(f"{failure}: {exc}") from exc
        if completed.returncode != 0:
            raise RootError(f"{failure}: {completed.stderr.strip()}")

    resolver(
        ["venv", "--python", str(pins.python), str(environment)],
        "cannot create the dependency environment",
    )
    if named:
        resolver(
            [
                "pip",
                "install",
                "--python",
                str(environment / "bin" / "python"),
                "--no-index",
                "--no-deps",
                *(str(path) for path in named),
            ],
            "cannot install the verified wheels",
        )
    _seal(environment)
    return environment
