"""Host-qualification guards shared by confinement acceptance suites."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
MANIFEST = REPOSITORY / "governance/confinement/native-launcher-build-v1.json"
CLONE_NEWUSER = 0x10000000


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def build_closure_limitation() -> str | None:
    """Return why this host cannot reproduce the pinned launcher build closure.

    Host qualification is absence, not success. A foreign host must exercise the
    controller's fail-closed build refusal rather than pretend its toolchain can
    prove the qualified host's launcher bytes.
    """

    try:
        manifest = json.loads(MANIFEST.read_bytes())
        inputs = manifest["build"]["inputs"]
        if not isinstance(inputs, list):
            raise TypeError("build.inputs is not a list")
        traced = [
            item
            for item in inputs
            if isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and Path(item["path"]).is_absolute()
        ]
        for item in traced:
            path = Path(item["path"])
            if not path.is_file():
                continue
            expected = item["sha256"]
            if not isinstance(expected, str):
                raise TypeError(f"build input {path} has no sha256 string")
            if _sha256_file(path) != expected:
                return (
                    "the pinned launcher build closure does not match this host "
                    f"(1 of {len(traced)} traced inputs differ, e.g. {path}) — "
                    "launcher-build refuses E-C17-BUILD-INPUT-DRIFT here"
                )
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as error:
        return (
            "the pinned launcher build manifest is unreadable "
            f"({type(error).__name__}: {error}) — "
            "launcher-build refuses E-C17-BUILD-INPUT-DRIFT here"
        )
    return None


def require_pinned_build_closure() -> None:
    """Stop host-only tests when the pinned build closure is absent."""

    limitation = build_closure_limitation()
    if limitation is not None:
        pytest.skip(f"SLICE-017 build host unavailable: {limitation}")


def userns_limitation() -> str | None:
    """Return why this host cannot create an unprivileged user namespace."""

    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.unshare.argtypes = [ctypes.c_int]
            libc.unshare.restype = ctypes.c_int
            if libc.unshare(CLONE_NEWUSER) == 0:
                os._exit(0)
            os.write(write_fd, str(ctypes.get_errno()).encode())
        finally:
            os.close(write_fd)
        os._exit(1)

    os.close(write_fd)
    try:
        reported_errno = os.read(read_fd, 32)
    finally:
        os.close(read_fd)
    _waited, status = os.waitpid(child, 0)
    if reported_errno in {
        str(errno.EPERM).encode(),
        str(errno.EACCES).encode(),
        str(errno.EINVAL).encode(),
    }:
        value = reported_errno.decode()
        return (
            f"unshare(CLONE_NEWUSER) denied (errno {value}) — "
            "confinement-session gates run on the qualified host"
        )
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, (
        "unshare(CLONE_NEWUSER) failed without a recognized host-qualification "
        f"errno: status={status}, reported_errno={reported_errno!r}"
    )
    return None


def require_unprivileged_userns() -> None:
    """Stop namespace-dependent tests when this host denies user namespaces."""

    limitation = userns_limitation()
    if limitation is not None:
        pytest.skip(f"SLICE-017/018 user-namespace host unavailable: {limitation}")


def require_delegated_userns_selftest(exit_code: int, stderr: str) -> None:
    """Stop sandbox tests for the known delegated user-namespace denial."""

    if (
        exit_code != 0
        and "Permission denied" in stderr
        and (
            "setgroups" in stderr
            or "uid_map" in stderr
            or "uid_map" in stderr.lower()
            or "map-user" in stderr
        )
    ):
        pytest.skip(
            "SLICE-017/018 user-namespace host unavailable: delegated "
            "setgroups/uid_map writes are denied — sandbox self-test cannot run "
            "here; gates run on the qualified host"
        )
