"""Validation and immutable materialisation primitives for runtime v3."""

from __future__ import annotations

import ctypes
import fcntl
import hashlib
import io
import json
import os
import re
import stat
import struct
from dataclasses import dataclass
from pathlib import Path

from ranex.foundation.canonical import canonical_json_bytes

try:
    from elftools.common.exceptions import ELFError
    from elftools.elf.elffile import ELFFile
except ImportError:  # pragma: no cover - dependency is pinned by pyproject
    ELFFile = None
    ELFError = Exception

_KINDS = ("loader", "entrypoint", "shared-library", "native-extension", "runtime-data")
_PREFIX = {"loader": "loader/", "entrypoint": "bin/", "shared-library": "lib/",
           "native-extension": "lib/", "runtime-data": "data/"}
_TAGS = ("rpath", "runpath", "filter", "auxiliary", "audit", "depaudit")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_LOADER_NAME = "ld-" + "linux-x86-64.so.2"
_LOADER_SELF_ID = "/lib64/" + _LOADER_NAME
_F_SEAL_WRITE = 0x0008
_F_SEAL_GROW = 0x0004
_F_SEAL_SHRINK = 0x0002
_F_SEAL_SEAL = 0x0001
_F_SEAL_EXEC = 0x0020
if not hasattr(fcntl, "F_ADD_SEALS"):
    fcntl.F_ADD_SEALS = 1033
    fcntl.F_GET_SEALS = 1034
for _name, _value in {"F_SEAL_WRITE": 8, "F_SEAL_GROW": 4, "F_SEAL_SHRINK": 2, "F_SEAL_SEAL": 1}.items():
    if not hasattr(fcntl, _name):
        setattr(fcntl, _name, _value)


def _seal_names(execute_allowed: bool) -> list[str]:
    names = ["WRITE", "GROW", "SHRINK"]
    if execute_allowed:
        names.append("FUTURE_WRITE")
    return [*names, "EXEC", "SEAL"]


@dataclass(frozen=True)
class RuntimeFile:
    path: str
    mode: str
    kind: str
    sha256: str
    elf: dict[str, object] | None


@dataclass(frozen=True)
class RuntimeManifest:
    value: dict[str, object]
    files: tuple[RuntimeFile, ...]


@dataclass(frozen=True)
class SealedRuntimeFile:
    descriptor: int
    creation_flags: int
    execute_allowed: bool


@dataclass(frozen=True)
class SealedRuntimeClosure:
    """All sealed authorities for one validated closure snapshot."""

    manifest_digest: str
    files: tuple[tuple[str, SealedRuntimeFile], ...]
    file_set: tuple[dict[str, object], ...]
    file_set_digest: str

    def close(self) -> None:
        for _path, sealed in self.files:
            os.close(sealed.descriptor)


def _path(path: object) -> str:
    if not isinstance(path, str) or not path or len(path) > 255 or path.startswith("/"):
        raise ValueError("canonical runtime path")
    parts = path.split("/")
    if len(parts) > 16 or any(not part or part in {".", ".."} for part in parts):
        raise ValueError("canonical runtime path")
    if any(len(part.encode()) > 255 for part in parts):
        raise ValueError("canonical runtime path")
    return path


def validate_runtime_rows(rows: list[dict[str, object]]) -> None:
    paths = []
    for row in rows:
        path = _path(row.get("path"))
        kind = row.get("kind")
        if kind not in _KINDS or path == "closure.json" or path in {"lib", "bin", "loader", "data"}:
            raise ValueError("runtime row kind or reserved path")
        if not path.startswith(_PREFIX[kind]):
            raise ValueError("runtime row kind prefix")
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate path")
    ordered = sorted(paths)
    if paths != ordered:
        raise ValueError("files are not sorted")
    pathset = set(paths)
    for path in paths:
        parents = path.split("/")[:-1]
        for index in range(1, len(parents) + 1):
            if "/".join(parents[:index]) in pathset:
                raise ValueError("ancestor collision")


def parse_runtime_manifest(raw: bytes) -> RuntimeManifest:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("manifest is not JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest must be an object")
    expected = {"schema", "architecture", "loader", "entrypoint", "library_paths", "files"}
    if set(value) != expected or value.get("schema") != "ranex-dynamic-runtime-closure-v1":
        raise ValueError("unknown manifest field")
    architecture = value["architecture"]
    if not isinstance(architecture, dict) or architecture != {
        "elf_class": 64, "endian": "little", "machine": "EM_X86_64",
        "osabi": "ELFOSABI_SYSV", "abi_version": 0}:
        raise ValueError("architecture")
    if value.get("library_paths") != ["lib"]:
        raise ValueError("library paths")
    loader = value["loader"]
    entry = value["entrypoint"]
    if not isinstance(loader, dict) or not isinstance(entry, dict):
        raise ValueError("loader or entrypoint")
    if set(loader) != {"path", "self_id", "version", "sha256"} or set(entry) != {
        "path", "pt_interp", "sha256"
    }:
        raise ValueError("loader or entrypoint shape")
    loader_path = _path(loader.get("path"))
    entry_path = _path(entry.get("path"))
    if (
        loader.get("self_id") != _LOADER_SELF_ID
        or loader.get("version") != "glibc-2.39"
        or entry.get("pt_interp") != loader.get("self_id")
        or not isinstance(loader.get("sha256"), str)
        or not _SHA.fullmatch(loader["sha256"])
        or not isinstance(entry.get("sha256"), str)
        or not _SHA.fullmatch(entry["sha256"])
    ):
        raise ValueError("loader or entrypoint binding")
    files = value["files"]
    if not isinstance(files, list) or len(files) > 511:
        raise ValueError("511")
    validate_runtime_rows(files)
    parsed: list[RuntimeFile] = []
    for row in files:
        if set(row) != {"path", "mode", "kind", "sha256", "elf"}:
            raise ValueError("unknown file field")
        if not isinstance(row["mode"], str) or not re.fullmatch(r"0[0-7]{3,4}", row["mode"]):
            raise ValueError("mode")
        if not isinstance(row["sha256"], str) or not _SHA.fullmatch(row["sha256"]):
            raise ValueError("digest")
        elf = row["elf"]
        native = row["kind"] != "runtime-data"
        if native != (elf is not None):
            raise ValueError("ELF kind")
        if elf is not None:
            if not isinstance(elf, dict): raise ValueError("elf")
            required = {"elf_class", "endian", "machine", "osabi", "abi_version", "type",
                        "pt_interp", "soname", "needed", *_TAGS}
            if set(elf) != required: raise ValueError("elf shape")
            for tag in _TAGS:
                if elf[tag] is not None: raise ValueError(tag.upper())
            if (
                elf["elf_class"] != 64
                or elf["endian"] != "little"
                or elf["machine"] != "EM_X86_64"
                or elf["osabi"] not in {"ELFOSABI_SYSV", "ELFOSABI_LINUX"}
                or elf["abi_version"] != 0
                or elf["type"] not in {"ET_EXEC", "ET_DYN"}
                or elf["pt_interp"] not in {None, loader["self_id"]}
                or (
                    elf["soname"] is not None
                    and (
                        not isinstance(elf["soname"], str)
                        or "/" in elf["soname"]
                        or "$" in elf["soname"]
                    )
                )
            ):
                raise ValueError("architecture or dynamic string")
            needed = elf["needed"]
            if (
                not isinstance(needed, list)
                or needed != sorted(set(needed))
                or any(not isinstance(x, str) or "/" in x or "$" in x for x in needed)
            ):
                raise ValueError("dynamic string")
        if row["mode"] != ("0555" if native else "0444"):
            raise ValueError("mode")
        parsed.append(RuntimeFile(row["path"], row["mode"], row["kind"], row["sha256"], elf))
    loader_rows = [item for item in parsed if item.kind == "loader"]
    entry_rows = [item for item in parsed if item.kind == "entrypoint"]
    if (
        len(loader_rows) != 1
        or len(entry_rows) != 1
        or loader_rows[0].path != loader_path
        or loader_rows[0].sha256 != loader["sha256"]
        or entry_rows[0].path != entry_path
        or entry_rows[0].sha256 != entry["sha256"]
        or entry_rows[0].elf is None
        or entry_rows[0].elf["pt_interp"] != loader["self_id"]
    ):
        raise ValueError("loader or entrypoint row")
    return RuntimeManifest(value, tuple(parsed))


def seal_runtime_file(source: Path, expected_sha256: str, *, kind: str, mode: int) -> SealedRuntimeFile:
    if kind not in _KINDS and kind != "manifest":
        raise ValueError("unknown runtime kind")
    if not isinstance(expected_sha256, str): raise ValueError("digest")
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(source_fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("runtime source is not regular")
        payload = bytearray()
        while block := os.read(source_fd, 1024 * 1024):
            payload.extend(block)
        after = os.fstat(source_fd)
    finally:
        os.close(source_fd)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("source changed during copy")
    actual = hashlib.sha256(payload).hexdigest()
    expected = expected_sha256.removeprefix("sha256:")
    if actual != expected: raise ValueError("runtime digest differs")
    if kind in {"loader", "entrypoint", "shared-library", "native-extension"} and payload.startswith(b"\x7fELF"):
        if ELFFile is None:
            raise ValueError("pyelftools is unavailable")
        try:
            elf = ELFFile(io.BytesIO(payload))
            dynamic = elf.get_section_by_name(".dynamic")
            if dynamic is not None and any(
                tag.entry.d_tag in {"DT_RPATH", "DT_RUNPATH", "DT_FILTER", "DT_AUXILIARY", "DT_AUDIT", "DT_DEPAUDIT"}
                for tag in dynamic.iter_tags()
            ):
                raise ValueError("forbidden ELF dynamic tag")
        except ValueError:
            raise
        except (ELFError, OSError, AttributeError, KeyError, IndexError, struct.error) as exc:
            raise ValueError("malformed ELF") from exc
    return seal_runtime_bytes(bytes(payload), kind=kind, mode=mode)


def seal_runtime_bytes(payload: bytes, *, kind: str, mode: int) -> SealedRuntimeFile:
    """Create one sealed descriptor using the runtime closure's shared mechanics."""

    native = kind in {"loader", "entrypoint", "shared-library", "native-extension"}
    allow = getattr(os, "MFD_EXEC", 0x0010) if native else getattr(os, "MFD_NOEXEC_SEAL", 0x0008)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_int
    fd = libc.syscall(319, b"ranex-runtime", 0x0002 | allow)
    if fd < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    try:
        os.write(fd, payload)
        os.fchmod(fd, mode)
        seals = _F_SEAL_WRITE | _F_SEAL_GROW | _F_SEAL_SHRINK | _F_SEAL_EXEC | _F_SEAL_SEAL
        if fcntl.fcntl(fd, fcntl.F_ADD_SEALS, seals) != 0:
            raise OSError("runtime seal installation failed")
        if _descriptor_hash(fd) != hashlib.sha256(payload).hexdigest():
            raise ValueError("post-seal digest differs")
    except Exception:
        os.close(fd)
        raise
    return SealedRuntimeFile(fd, allow, native)


def create_runtime_memfd(name: bytes, flags: int) -> int:
    """Create a memfd through the pinned x86-64 Linux syscall interface."""

    if not name or b"\x00" in name:
        raise ValueError("memfd name")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_int
    descriptor = libc.syscall(319, name, flags)
    if descriptor < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return descriptor


def seal_runtime_closure(root: Path, raw_manifest: bytes) -> SealedRuntimeClosure:
    """Seal every manifest object and return the exact launcher handoff set."""
    manifest = parse_runtime_manifest(raw_manifest)
    expected_paths = {item.path for item in manifest.files} | {"closure.json"}
    actual_paths: set[str] = set()
    for source in root.rglob("*"):
        relative = source.relative_to(root).as_posix()
        facts = os.lstat(source)
        if stat.S_ISDIR(facts.st_mode):
            continue
        if not stat.S_ISREG(facts.st_mode):
            raise ValueError(f"runtime source is not regular: {relative}")
        actual_paths.add(relative)
    if actual_paths != expected_paths:
        raise ValueError("runtime source coverage differs from manifest")
    rows: list[tuple[str, SealedRuntimeFile]] = []
    report_rows: list[dict[str, object]] = []
    try:
        for item in manifest.files:
            sealed = seal_runtime_file(
                root / item.path,
                item.sha256,
                kind=item.kind,
                mode=int(item.mode, 8),
            )
            rows.append((item.path, sealed))
            report_rows.append(
                {
                    "path": item.path,
                    "mode": item.mode,
                    "kind": item.kind,
                    "sha256": item.sha256,
                    "elf": item.elf,
                    "seals": _seal_names(sealed.execute_allowed),
                    "mount_attributes": (
                        ["RDONLY", "NOEXEC"]
                        if not sealed.execute_allowed
                        else ["RDONLY"]
                    ),
                }
            )
        manifest_sealed = seal_runtime_file(
            root / "closure.json",
            hashlib.sha256(raw_manifest).hexdigest(),
            kind="manifest",
            mode=0o444,
        )
        rows.append(("closure.json", manifest_sealed))
        report_rows.append(
            {
                "path": "closure.json",
                "mode": "0444",
                "kind": "manifest",
                "sha256": "sha256:" + hashlib.sha256(raw_manifest).hexdigest(),
                "elf": None,
                "seals": _seal_names(False),
                "mount_attributes": ["RDONLY", "NOEXEC"],
            }
        )
        ordered = tuple(sorted(report_rows, key=lambda row: str(row["path"])))
        return SealedRuntimeClosure(
            hashlib.sha256(raw_manifest).hexdigest(),
            tuple(sorted(rows)),
            ordered,
            hashlib.sha256(canonical_json_bytes(ordered)).hexdigest(),
        )
    except Exception:
        for _path, sealed in rows:
            os.close(sealed.descriptor)
        raise


def expected_runtime_file_set(
    manifest: RuntimeManifest, raw_manifest: bytes
) -> tuple[dict[str, object], ...]:
    """Derive the exact result rows without creating launcher authorities."""

    rows: list[dict[str, object]] = []
    for item in manifest.files:
        rows.append(
            {
                "path": item.path,
                "mode": item.mode,
                "kind": item.kind,
                "sha256": item.sha256,
                "elf": item.elf,
                "seals": _seal_names(
                    item.kind
                    in {"loader", "entrypoint", "shared-library", "native-extension"}
                ),
                "mount_attributes": (
                    ["RDONLY"]
                    if item.kind
                    in {"loader", "entrypoint", "shared-library", "native-extension"}
                    else ["RDONLY", "NOEXEC"]
                ),
            }
        )
    rows.append(
        {
            "path": "closure.json",
            "mode": "0444",
            "kind": "manifest",
            "sha256": "sha256:" + hashlib.sha256(raw_manifest).hexdigest(),
            "elf": None,
            "seals": _seal_names(False),
            "mount_attributes": ["RDONLY", "NOEXEC"],
        }
    )
    return tuple(sorted(rows, key=lambda row: str(row["path"])))


def parsed_runtime_graph(
    root: Path,
    manifest: RuntimeManifest,
    descriptors: dict[str, int] | None = None,
) -> list[dict[str, object]]:
    """Derive the graph from sealed descriptors, or paths for test tooling."""
    if ELFFile is None:
        raise ValueError("pyelftools is unavailable")
    result: list[dict[str, object]] = []
    for item in manifest.files:
        if item.elf is None:
            continue
        try:
            handle = (
                os.fdopen(os.dup(descriptors[item.path]), "rb")
                if descriptors is not None
                else (root / item.path).open("rb")
            )
            with handle:
                elf = ELFFile(handle)
                dynamic = elf.get_section_by_name(".dynamic")
                if dynamic is None:
                    raise ValueError("native runtime object has no dynamic section")
                tags = list(dynamic.iter_tags())
                needed = sorted(
                    str(tag.needed)
                    for tag in tags
                    if tag.entry.d_tag == "DT_NEEDED"
                )
                sonames = [str(tag.soname) for tag in tags if tag.entry.d_tag == "DT_SONAME"]
                interps = [
                    segment.get_interp_name()
                    for segment in elf.iter_segments()
                    if segment.header.p_type == "PT_INTERP"
                ]
                actual = {
                    "elf_class": elf.elfclass,
                    "endian": "little" if elf.little_endian else "big",
                    "machine": elf.header.e_machine,
                    "osabi": elf.header.e_ident.EI_OSABI,
                    "abi_version": elf.header.e_ident.EI_ABIVERSION,
                    "type": elf.header.e_type,
                    "pt_interp": interps[0] if len(interps) == 1 else None,
                    "soname": sonames[0] if len(sonames) == 1 else None,
                    "needed": needed,
                    **{
                        name: next(
                            (
                                str(tag.entry.d_val)
                                for tag in tags
                                if tag.entry.d_tag == "DT_" + name.upper()
                            ),
                            None,
                        )
                        for name in _TAGS
                    },
                }
        except (OSError, AttributeError, ValueError) as exc:
            raise ValueError(f"cannot parse ELF {item.path}: {exc}") from exc
        if actual != item.elf:
            raise ValueError(f"ELF metadata differs for {item.path}")
        result.append({"path": item.path, "needed": needed})
    return sorted(result, key=lambda row: str(row["path"]))


def expected_realized_graph(manifest: RuntimeManifest) -> dict[str, dict[str, object]]:
    """Build the loader report expectation from the manifest's closed graph."""
    by_name: dict[str, str] = {}
    for item in manifest.files:
        if item.elf is None:
            continue
        names = {Path(item.path).name}
        soname = item.elf.get("soname")
        if isinstance(soname, str):
            names.add(soname)
        for name in names:
            if name in by_name and by_name[name] != item.path:
                raise ValueError(f"ambiguous runtime object {name}")
            by_name[name] = item.path
    graph = {row["path"]: row["needed"] for row in parsed_runtime_graph_from_manifest(manifest)}
    roots = [manifest.value["entrypoint"]["path"]] + [
        item.path for item in manifest.files if item.kind == "native-extension"
    ]
    expected: dict[str, dict[str, object]] = {}
    for root in sorted(roots):
        resolved: dict[str, str] = {}
        pending = list(graph.get(root, []))
        while pending:
            name = pending.pop(0)
            path = by_name.get(name)
            if path is None:
                raise ValueError(f"unresolved runtime dependency {name}")
            if path == manifest.value["loader"]["path"]:
                continue
            if name in resolved:
                continue
            resolved[name] = "/ranex/runtime/" + path
            pending.extend(graph.get(path, []))
        expected[root] = {
            "loader": "/ranex/runtime/" + str(manifest.value["loader"]["path"]),
            "synthetic": ["linux-vdso.so.1"] if resolved else [],
            "resolved": dict(sorted(resolved.items())),
        }
    return expected


def parsed_runtime_graph_from_manifest(manifest: RuntimeManifest) -> list[dict[str, object]]:
    """Return the manifest-declared graph when source bytes are unavailable."""
    return [
        {"path": item.path, "needed": sorted(item.elf["needed"])}
        for item in manifest.files
        if item.elf is not None
    ]


def parsed_graph_digest(rows: list[dict[str, object]]) -> str:
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def realized_graph_digest(rows: list[dict[str, object]]) -> str:
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def expected_realized_runtime_graph(manifest: RuntimeManifest) -> list[dict[str, object]]:
    """Derive the exact normalized loader-report graph from closed authority."""
    expected = expected_realized_graph(manifest)
    entrypoint = str(manifest.value["entrypoint"]["path"])
    loader = manifest.value["loader"]
    rows: list[dict[str, object]] = []
    for root, report in sorted(expected.items()):
        resolved = [
            {"name": name, "path": path.removeprefix("/ranex/runtime/")}
            for name, path in report["resolved"].items()
        ]
        # glibc's --list output names the PT_INTERP loader as a resolved edge
        # for an executable, while shared-object roots print the loader without
        # the `name => path` form consumed by realized_runtime_graph_from_reports.
        if root == entrypoint:
            resolved.append(
                {
                    "name": str(loader["self_id"]),
                    "path": str(loader["path"]),
                }
            )
        rows.append(
            {
                "root": root,
                "resolved": sorted(resolved, key=lambda row: str(row["name"])),
            }
        )
    return rows


def realized_runtime_graph_from_reports(reports: dict[str, bytes]) -> list[dict[str, object]]:
    """Project validated loader reports into their canonical realized edges."""
    rows: list[dict[str, object]] = []
    for root, raw in sorted(reports.items()):
        normalized = normalize_loader_report(raw, "/ranex/runtime/" + root)
        resolved = [
            {"name": name, "path": path.removeprefix("/ranex/runtime/")}
            for name, path in normalized["resolved"].items()
        ]
        decoded = raw.decode("utf-8")
        for line in decoded.splitlines():
            match = re.match(r"^\s*(\S+)\s+=>\s+(\S+)\s+\(0x[0-9a-fA-F]+\)\s*$", line)
            if match is None:
                continue
            name, path = match.groups()
            if path == normalized["loader"]:
                resolved.append(
                    {"name": name, "path": path.removeprefix("/ranex/runtime/")}
                )
        rows.append({"root": root, "resolved": sorted(resolved, key=lambda row: str(row["name"]))})
    return rows


def _descriptor_hash(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024): digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest()


def normalize_loader_report(raw: bytes, root_entrypoint: str | None = None) -> dict[str, object]:
    if len(raw) == 0 or len(raw) > 65536: raise ValueError("malformed report")
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"non-UTF-8 loader report: {raw[:128].hex()}") from exc
    if decoded.strip() == "statically linked":
        if root_entrypoint is None:
            raise ValueError("malformed report")
        return {
            "loader": "/ranex/runtime/loader/" + _LOADER_NAME,
            "synthetic": [],
            "resolved": {},
        }
    loader = None; synthetic: list[str] = []; resolved: dict[str, str] = {}
    consumed_program = False
    for line in decoded.splitlines():
        match = re.match(r"^\s*(\S+)(?:\s+=>\s+(\S+))?\s+\(0x[0-9a-fA-F]+\)\s*$", line)
        if not match: raise ValueError("malformed report")
        name, path = match.groups()
        if path is None and root_entrypoint is not None and name == root_entrypoint and not consumed_program:
            consumed_program = True
            continue
        if name == "linux-vdso.so.1":
            if synthetic: raise ValueError("duplicate vdso")
            synthetic.append(name); continue
        target = path or name
        if not target.startswith("/ranex/runtime/"): raise ValueError("outside runtime")
        if target.endswith("/loader/" + _LOADER_NAME): loader = target
        elif path is not None:
            if name in resolved: raise ValueError("duplicate resolution")
            resolved[name] = target
        else: raise ValueError("malformed report")
    if loader is None or synthetic != ["linux-vdso.so.1"]: raise ValueError("loader/vdso")
    return {"loader": loader, "synthetic": synthetic, "resolved": resolved}
