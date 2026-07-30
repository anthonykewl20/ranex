from __future__ import annotations

import errno
import hashlib
import hmac
import os
import stat
from dataclasses import replace
from pathlib import Path

from ranex.assurance.api.contracts import EvidenceRecord


class EvidenceArtifactError(ValueError):
    """The referenced artifact cannot serve as verified evidence."""


def _open_flags(*, directory: bool) -> int:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(
            os,
            "O_NOFOLLOW",
            0,
        )
    )
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    else:
        flags |= getattr(os, "O_NONBLOCK", 0)
    return flags


def _open_artifact_descriptor(
    evidence_root: Path,
    relative: Path,
) -> tuple[int, list[int]]:
    opened: list[int] = []
    try:
        directory_fd = os.open(evidence_root, _open_flags(directory=True))
        opened.append(directory_fd)
        for component in relative.parts[:-1]:
            directory_fd = os.open(
                component,
                _open_flags(directory=True),
                dir_fd=directory_fd,
            )
            opened.append(directory_fd)
        artifact_fd = os.open(
            relative.parts[-1],
            _open_flags(directory=False),
            dir_fd=directory_fd,
        )
        opened.append(artifact_fd)
        return artifact_fd, opened
    except OSError as exc:
        for descriptor in reversed(opened):
            os.close(descriptor)
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise EvidenceArtifactError(
                "artifact path contains a symlink or non-directory component"
            ) from exc
        raise EvidenceArtifactError("artifact path cannot be opened safely") from exc


def _sha256_descriptor(
    descriptor: int,
) -> tuple[str, os.stat_result, os.stat_result]:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise EvidenceArtifactError("artifact must be a regular file")

    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while chunk := os.read(descriptor, 1024 * 1024):
        digest.update(chunk)
    after = os.fstat(descriptor)
    return digest.hexdigest(), before, after


def _stable_file(before: os.stat_result, after: os.stat_result) -> bool:
    return (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )


def verify_evidence_artifact(
    evidence: EvidenceRecord,
    *,
    artifact_path: str,
    evidence_root: Path,
) -> EvidenceRecord:
    """Hash the same race-safe descriptor opened beneath a trusted root."""
    relative = Path(artifact_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(component in {"", ".", ".."} for component in relative.parts)
    ):
        raise EvidenceArtifactError(
            "artifact_path must be a contained relative path without traversal"
        )

    artifact_fd, opened = _open_artifact_descriptor(evidence_root, relative)
    try:
        observed_digest, before, after = _sha256_descriptor(artifact_fd)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)

    if not _stable_file(before, after):
        raise EvidenceArtifactError("artifact changed while it was being verified")
    expected_digest = evidence.artifact_sha256.removeprefix("sha256:")
    if not hmac.compare_digest(observed_digest, expected_digest):
        raise EvidenceArtifactError("artifact digest does not match evidence record")

    return replace(evidence, artifact_verified=True)
