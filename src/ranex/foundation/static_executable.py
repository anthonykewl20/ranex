"""Validation shared by strict-local static worker admission paths."""

from __future__ import annotations

import os
import struct
from pathlib import Path


def inspect_self_contained_static_executable(descriptor: int, path: Path) -> None:
    """Admit only the ELF64 ET_EXEC/no-runtime-closure shape frozen by v2."""

    try:
        header = os.pread(descriptor, 64, 0)
    except OSError as exc:
        raise ValueError(f"cannot inspect static executable {path}: {exc}") from exc
    if len(header) != 64 or header[:6] != b"\x7fELF\x02\x01":
        raise ValueError("v2 worker is not a little-endian ELF64 executable")
    elf_type, machine = struct.unpack_from("<HH", header, 16)
    program_offset = struct.unpack_from("<Q", header, 32)[0]
    program_size, program_count = struct.unpack_from("<HH", header, 54)
    if elf_type != 2 or machine != 62 or program_size < 56 or program_count == 0:
        raise ValueError("v2 worker is not a self-contained x86-64 ET_EXEC object")
    for index in range(program_count):
        offset = program_offset + index * program_size
        try:
            program = os.pread(descriptor, program_size, offset)
        except OSError as exc:
            raise ValueError(f"cannot inspect static executable {path}: {exc}") from exc
        if len(program) != program_size:
            raise ValueError("v2 worker has a truncated ELF program table")
        kind = struct.unpack_from("<I", program, 0)[0]
        if kind in {2, 3}:  # PT_DYNAMIC or PT_INTERP from the installed ELF64 ABI.
            raise ValueError("v2 worker requests an unsupported dynamic runtime closure")
