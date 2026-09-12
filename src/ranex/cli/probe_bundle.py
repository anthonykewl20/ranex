"""Freeze committed probe bytes into A/B-bound bundles, never product verdicts.

The operator pins B independently. This is artifact integrity, not execution,
approval issuance, OS isolation, or a claim that a supplied probe is meaningful.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import sys
from pathlib import Path

from ranex.cli.repository import committable_into, git, uncommitted_paths
from ranex.cli.subject import SubjectError, _tree_entries, _verified_blob
from ranex.foundation.canonical import command_digest
from ranex.foundation.specification_abc import (
    SpecificationABCError,
    canonical_payload_bytes,
    parse_canonical_payload,
    payload_digest,
    validate_generated_artifact_manifest,
    validate_spec_packet,
)

_PATH = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*(?:/[A-Za-z0-9_-][A-Za-z0-9._-]*)*\Z")
_CATEGORIES = ("pseudocode_flow", "protected", "expected_values", "baselines",
               "negative_controls", "trace_projections", "sidecars")
_DESCRIPTOR = "probe-contract.json"


def _refuse(code: str, detail: str) -> None:
    raise ValueError(f"E-PROBE-{code}: {detail}")


def _path(value: object) -> str:
    if (not isinstance(value, str) or not _PATH.fullmatch(value)
            or any(part in {".", "..", ".git"} for part in value.split("/"))):
        _refuse("PATH", "probe paths must be portable relative names")
    return value


def _roots(value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        _refuse("ROOTS", "at least one complete probe root is required")
    roots = sorted(_path(item) for item in value)
    for index, root in enumerate(roots):
        if any(root == prior or root.startswith(prior + "/") for prior in roots[:index]):
            _refuse("ROOTS", "duplicate or overlapping probe roots")
    return roots


def _argv(value: object) -> list[str]:
    if (not isinstance(value, list) or not value
            or any(not isinstance(arg, str) or "\0" in arg for arg in value)
            or not value[0]):
        _refuse("ARGV", "a nonempty literal argv array is required")
    return value


def _hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _selected(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(root + "/") for root in roots)


def _snapshot(root: Path, roots: list[str]) -> tuple[str, list[dict], dict[str, bytes]]:
    if uncommitted_paths(root):
        _refuse("DIRTY", "commit the candidate before freezing or checking probes")
    resolved = git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if resolved.returncode:
        _refuse("SUBJECT", "HEAD must name a commit")
    commit = resolved.stdout.strip()
    files: dict[str, bytes] = {}
    rows = []
    for entry in sorted(_tree_entries(root, commit, git), key=lambda item: item.path):
        if not _selected(entry.path, roots):
            continue
        _path(entry.path)
        content = _verified_blob(root, entry, git)
        if b"ranex-gauge: placeholder-until-execution-slice" in content:
            _refuse("PLACEHOLDER", "projection placeholders cannot be frozen as executable probes")
        files[entry.path] = content
        rows.append({"path": entry.path, "mode": entry.mode, "digest": _hash(content)})
    for selected in roots:
        if not any(_selected(path, [selected]) for path in files):
            _refuse("ABSENT", f"probe root is empty or absent: {selected}")
    if git(root, "rev-parse", "HEAD").stdout.strip() != commit or uncommitted_paths(root):
        _refuse("DRIFT", "repository changed while reading probe objects")
    return commit, rows, files


def _manifest(packet: dict, descriptor: bytes, files: dict[str, bytes], argv: list[str]) -> dict:
    artifacts: dict[str, object] = {category: [] for category in _CATEGORIES}
    artifacts["protected"] = [
        {"path": path, "digest": _hash(raw)}
        for path, raw in sorted({_DESCRIPTOR: descriptor,
                                **{"probes/" + path: raw for path, raw in files.items()}}.items())
    ]
    artifacts["invocation"] = {"argv": argv}
    manifest = {"version": "generated-artifact-manifest-v1", "domain": packet["domain"],
                "a_digest": payload_digest(packet), "artifacts": artifacts, "exemptions": []}
    return validate_generated_artifact_manifest(manifest, spec_packet=packet)


def _regular_read(root: Path, relative: str, *, executable: bool = False) -> bytes:
    # Walk descriptors, not resolved paths: reject symlinks even within the bundle,
    # and never open a FIFO/device supplied in place of a regular artifact.
    parts = _path(relative).split("/")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            mode = os.fstat(stream.fileno()).st_mode
            if not stat.S_ISREG(mode):
                _refuse("FILE", "bundle artifacts must be regular files")
            if bool(mode & 0o111) != executable or mode & 0o6000:
                _refuse("MODE", "bundle executable mode differs from frozen B")
            return stream.read()
    finally:
        os.close(directory)


def freeze_bundle(root: Path, packet_path: Path, invocation_path: Path,
                  roots: list[str], output: Path) -> dict:
    output = output.absolute()
    if output.is_symlink() or output != output.resolve():
        _refuse("OUTPUT", "bundle output must not traverse symlinks")
    if committable_into(output, root):
        _refuse("OUTPUT", "bundle must be outside the candidate repository and its worktrees")
    packet = validate_spec_packet(parse_canonical_payload(packet_path.read_bytes()))
    argv = _argv(parse_canonical_payload(invocation_path.read_bytes()))
    roots = _roots(roots)
    commit, entries, files = _snapshot(root, roots)
    descriptor = canonical_payload_bytes({"version": "probe-bundle-v1", "base_commit": commit,
                                          "roots": roots, "entries": entries, "argv": argv})
    manifest = _manifest(packet, descriptor, files, argv)
    # Exclusive directory creation: no partial overwrite or merge with an older
    # freeze. A failed construction is removed; an existing output is untouched.
    output.mkdir(mode=0o700)
    try:
        contents = {"spec-packet.json": canonical_payload_bytes(packet),
                    "manifest.json": canonical_payload_bytes(manifest), _DESCRIPTOR: descriptor,
                    **{"probes/" + path: raw for path, raw in files.items()}}
        modes = {"probes/" + row["path"]: row["mode"] for row in entries}
        for relative, raw in contents.items():
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(raw)
            destination.chmod(0o700 if modes.get(relative) == "100755" else 0o600)
    except BaseException:
        shutil.rmtree(output)
        raise
    return {"status": "FROZEN", "manifest_digest": payload_digest(manifest),
            "a_digest": payload_digest(packet), "base_commit": commit,
            "command_digest": command_digest(argv), "files": len(entries)}


def check_bundle(root: Path, bundle: Path, expected_digest: str) -> dict:
    bundle = bundle.absolute()
    if bundle.is_symlink() or bundle != bundle.resolve() or committable_into(bundle, root):
        _refuse("BUNDLE", "bundle must be external and must not traverse symlinks")
    packet = validate_spec_packet(parse_canonical_payload(_regular_read(bundle, "spec-packet.json")))
    manifest = validate_generated_artifact_manifest(
        parse_canonical_payload(_regular_read(bundle, "manifest.json")), spec_packet=packet)
    if payload_digest(manifest) != expected_digest:
        _refuse("PIN", "B does not match the independently supplied manifest digest")
    raw = _regular_read(bundle, _DESCRIPTOR)
    descriptor = parse_canonical_payload(raw)
    if (not isinstance(descriptor, dict)
            or set(descriptor) != {"version", "base_commit", "roots", "entries", "argv"}
            or descriptor["version"] != "probe-bundle-v1"
            or not isinstance(descriptor["base_commit"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", descriptor["base_commit"])):
        _refuse("SHAPE", "invalid probe bundle descriptor")
    roots = _roots(descriptor["roots"])
    argv = _argv(descriptor["argv"])
    commit, rows, files = _snapshot(root, roots)
    if rows != descriptor["entries"]:
        _refuse("DRIFT", "probe root membership, executable modes or bytes changed")
    # Reconstruct B from the candidate snapshot. This also rejects malformed or
    # missing descriptor rows, alternate invocations, extra categories/exemptions.
    if _manifest(packet, raw, files, argv) != manifest:
        _refuse("MANIFEST", "bundle contents or invocation differ from frozen B")
    modes = {row["path"]: row["mode"] for row in rows}
    for path, content in files.items():
        if _regular_read(bundle, "probes/" + path, executable=modes[path] == "100755") != content:
            _refuse("BYTES", "stored probe bytes differ from frozen B")
    expected = {"spec-packet.json", "manifest.json", _DESCRIPTOR,
                *("probes/" + path for path in files)}
    observed = set()
    for parent, directories, names in os.walk(bundle, followlinks=False):
        if any((Path(parent) / name).is_symlink() for name in directories):
            _refuse("FILE", "bundle directories must not be symlinks")
        observed.update((Path(parent) / name).relative_to(bundle).as_posix() for name in names)
    if observed != expected:
        _refuse("EXTRA", "bundle contains missing or additional artifacts")
    return {"status": "PROBES-UNCHANGED", "manifest_digest": expected_digest,
            "candidate_commit": commit, "command_digest": command_digest(argv), "files": len(rows)}


def cmd_probes(args: argparse.Namespace) -> int:
    from ranex.cli.main import _command_repository

    try:
        root = _command_repository(args)
        if args.action == "freeze-probes":
            result = freeze_bundle(root, Path(args.spec_packet), Path(args.invocation),
                                   args.root, Path(args.output))
        else:
            result = check_bundle(root, Path(args.bundle), args.manifest_digest)
    except (OSError, ValueError, SubjectError, SpecificationABCError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return 2
    print(canonical_payload_bytes(result).decode())
    return 0


def register(commands: argparse._SubParsersAction) -> None:
    freeze = commands.add_parser("freeze-probes", help="freeze committed probe bytes; no execution")
    freeze.add_argument("--spec-packet", required=True)
    freeze.add_argument("--invocation", required=True, help="canonical JSON argv file")
    freeze.add_argument("--root", action="append", required=True, help="complete file/directory root")
    freeze.add_argument("--output", required=True, help="new external bundle directory")
    check = commands.add_parser("check-probes", help="check frozen probe integrity; not a verdict")
    check.add_argument("--bundle", required=True)
    check.add_argument("--manifest-digest", required=True, help="independently trusted B digest")
    for command in (freeze, check):
        command.add_argument("--external-repository")
        command.set_defaults(func=cmd_probes)
