"""Regenerate the lock from the manifest alone, under pinned inputs.

The committed lock is never an input here — uv documents that an existing
lock is used as a preference, and `uv lock --check` accepted a deliberately
fabricated wheel hash (ADR-007). So the manifest is copied into an empty
directory, the pinned resolver regenerates the lock from nothing, and the
caller compares complete bytes. Both the graph and every artifact hash bind,
because they are all bytes of the same file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ranex.cli.toolchain import pinned_path_value
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.pins import ResolutionPins


class DerivationError(ProvisioningError):
    """The committed lock cannot be reproduced from its manifest."""


def derive_lock(
    manifest: bytes,
    pins: ResolutionPins,
    resolver_descriptor: int,
    scratch: Path,
) -> bytes:
    """Resolve the manifest in an empty directory and return the lock bytes.

    The resolver runs through the already-verified descriptor, so the bytes
    that resolve are the bytes that were hashed against the pin. The scratch
    HOME and cache start empty: ambient uv configuration and a same-uid
    cache are both agent-writable state, and either sitting in front of this
    resolution would let the agent steer what "clean" derives to.
    """

    workspace = scratch / "derive"
    home = scratch / "home"
    cache = scratch / "cache"
    for directory in (workspace, home, cache):
        directory.mkdir(parents=True, exist_ok=True)
    (workspace / "pyproject.toml").write_bytes(manifest)

    arguments = [
        "uv",
        "lock",
        "--exclude-newer",
        pins.exclude_newer,
        "--python",
        str(pins.python),
        "--index-url",
        pins.indexes[0],
    ]
    for index in pins.indexes[1:]:
        arguments.extend(["--extra-index-url", index])

    try:
        completed = subprocess.run(
            arguments,
            executable=f"/proc/self/fd/{resolver_descriptor}",
            pass_fds=(resolver_descriptor,),
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
            env={
                "PATH": pinned_path_value(),
                "HOME": str(home),
                "UV_NO_CONFIG": "1",
                "UV_CACHE_DIR": str(cache),
                "UV_PYTHON_DOWNLOADS": "never",
            },
        )
    except OSError as exc:
        raise DerivationError(f"cannot run the pinned resolver: {exc}") from exc
    if completed.returncode != 0:
        raise DerivationError(
            f"clean resolution failed: {completed.stderr.strip()}"
        )
    try:
        return (workspace / "uv.lock").read_bytes()
    except OSError as exc:
        raise DerivationError(
            f"the resolver reported success but wrote no lock: {exc}"
        ) from exc


def refuse_mismatch(committed: bytes, derived: bytes) -> None:
    """Byte equality or refusal — with the first divergence shown, not hidden."""

    if committed == derived:
        return
    committed_lines = committed.decode("utf-8", "replace").splitlines()
    derived_lines = derived.decode("utf-8", "replace").splitlines()
    detail = "the files differ in length"
    for number, (ours, theirs) in enumerate(
        zip(committed_lines, derived_lines, strict=False),  # truncate to common prefix; length mismatch handled above
        start=1,
    ):
        if ours != theirs:
            detail = (
                f"first divergence at line {number}: committed {ours!r}, "
                f"derived {theirs!r}"
            )
            break
    raise DerivationError(
        "the committed uv.lock differs from a clean derivation of the "
        f"committed manifest under the pinned inputs; {detail}. A lock that "
        "cannot be reproduced was not produced by this manifest and these "
        "pins — re-lock deliberately, or find what moved"
    )
