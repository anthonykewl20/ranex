"""Durable, descriptor-relative atomic publication."""

from __future__ import annotations

import os
import uuid
from pathlib import Path


def _open_created_directory(root: Path, directory: Path) -> int:
    root = Path(root).absolute()
    directory = Path(directory).absolute()
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise OSError(f"directory is outside trusted root: {directory}") from exc
    if ".." in relative.parts:
        raise OSError(f"directory escapes trusted root: {directory}")
    descriptor = os.open(
        root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        for component in relative.parts:
            try:
                os.mkdir(component, 0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            following = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = following
        return descriptor
    except OSError:
        os.close(descriptor)
        raise


def write_atomic(target: Path, data: bytes, *, root: Path) -> None:
    target = Path(target).absolute()
    parent = _open_created_directory(root, target.parent)
    temporary = f".{target.name}.{uuid.uuid4().hex}"
    backup = f".{target.name}.{uuid.uuid4().hex}.backup"
    descriptor = -1
    had_previous = False
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                             0o444, dir_fd=parent)
        os.fchmod(descriptor, 0o444)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("atomic write made no progress")
            view = view[written:]
        os.fsync(descriptor)
        try:
            os.link(target.name, backup, src_dir_fd=parent, dst_dir_fd=parent,
                    follow_symlinks=False)
            had_previous = True
        except FileNotFoundError:
            pass
        os.replace(temporary, target.name, src_dir_fd=parent, dst_dir_fd=parent)
        try:
            os.fsync(parent)
        except OSError:
            if had_previous:
                os.replace(backup, target.name, src_dir_fd=parent, dst_dir_fd=parent)
            else:
                os.unlink(target.name, dir_fd=parent)
            os.fsync(parent)
            raise
        if had_previous:
            os.unlink(backup, dir_fd=parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=parent)
        except FileNotFoundError:
            pass
        try:
            os.unlink(backup, dir_fd=parent)
        except FileNotFoundError:
            pass
        finally:
            os.close(parent)
