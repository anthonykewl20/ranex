"""The architecture-freeze scanner: import edges against an approved graph.

A human-approved ADR names the modules of a package and the import edges
between them; this scanner is the deterministic counterweight that keeps that
naming true. Pure `ast` — no model, no network, no judgement about whether a
module is *good*; it answers one AST-decidable question per import statement:
is this edge in the approved set? The freeze is default-deny, so an internal
edge the freeze does not list is a finding, exactly as an absent test is
absence: an empty allow-list blocks everything rather than nothing.

The freeze (`ranex-architecture-freeze-v1`) is a committed governance file —
seam C, a trust root or a hole — and is digest-bound from the claim's argv:
the catalog that names the scanner also pins `--expected-freeze-digest`, so
editing the freeze without editing the catalog is itself a finding
(`arch/freeze-tampered`), not a silent policy change. Updating the freeze is
promote-ship work that moves both bytes together in one reviewed commit.

What it emits, all through the #97 fingerprint so regions bind to the
subject's bytes:

  arch/forbidden-import   `error`  an internal import edge not in
                                   `allowed_edges`
  arch/freeze-tampered    `error`  the freeze's canonical bytes do not hash
                                   to the digest the catalog pinned

Two shapes are refusals, not findings, because the closed scan summary has
no vocabulary that could block them: a `.py` file under `package_root` that
belongs to no freeze module makes the scan exit 2 naming the file (the
module-set analog of `missing` — a finding on an out-of-scope path is
invisible to the frozen universe, and a gate that cannot block is refused at
construction), and so does a file the walk cannot parse. Both leave no
artifact, so absence blocks, and neither can ever be accepted: the only
remedy is a freeze update, which is promote-ship work under the digest pin.

v1 semantics, stated so review can check them: an import names its most
specific target — `from pkg import policy` is an edge to `policy`, not also
to the package root's `__init__`; an import that resolves to no file the
subject carries is not an architecture edge (a broken import is the suite's
failure, not the graph's); a statement importing two targets on one line
shares one finding ID, because the ID binds the region, and acceptance is
review's answer to that statement. Only direct edges — the transitive shapes
(grimp's chain queries) are a studied extension, not shipped.

Like markers and antislop, the scanner exits 0 however many findings it
reports and decides through its artifact, and runs as the kernel's own
installed console script, `ranex-arch` — never a script the observed tree
carries (#110 Correction 2). The console script is load-bearing, not
cosmetic: a governed run resolves argv[0] once and executes the resolved
path, and a `-m` module form resolved through the venv symlink loses the
site-packages that carry the kernel itself.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict, cast

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import fingerprint

FREEZE_SCHEMA = "ranex-architecture-freeze-v1"

RULE_FORBIDDEN = "arch/forbidden-import"
RULE_TAMPERED = "arch/freeze-tampered"

#: The same exclusion set markers and antislop made deterministic.
SKIPPED_DIRECTORIES = frozenset(
    {".git", "node_modules", "build", "dist", "target", "__pycache__"}
)

_RULES = (
    (RULE_FORBIDDEN, "error", "an import edge the approved freeze does not list"),
    (RULE_TAMPERED, "error", "freeze bytes that do not match the pinned digest"),
)

_FREEZE_KEYS = {"schema", "approved_by", "package_root", "modules", "allowed_edges"}
_MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ArchitectureFreeze(TypedDict):
    """The approved graph: modules as path prefixes, edges as name pairs."""

    schema: str
    approved_by: str
    package_root: str
    modules: dict[str, str]
    allowed_edges: list[list[str]]


@dataclass(frozen=True, slots=True)
class ArchFinding:
    """One structural finding, bound to the subject's bytes."""

    rule_id: str
    path: str
    line: int
    snippet: str
    fingerprint: str

    @property
    def finding_id(self) -> str:
        return f"{self.path}::{self.rule_id}::{self.fingerprint}"


def _confined_relative(candidate: object) -> bool:
    """A freeze path names something inside the subject, and only that."""

    if not isinstance(candidate, str) or not candidate or candidate != candidate.strip():
        return False
    path = Path(candidate)
    return not path.is_absolute() and not any(part in {"..", ""} for part in path.parts)


def validate_architecture_freeze(value: object) -> ArchitectureFreeze:
    """Return a canonical architecture freeze, or refuse its exact shape."""

    if not isinstance(value, dict) or set(value) != _FREEZE_KEYS:
        raise ValueError(
            f"architecture freeze must contain exactly {sorted(_FREEZE_KEYS)}"
        )
    if value["schema"] != FREEZE_SCHEMA:
        raise ValueError(f"architecture freeze schema must be {FREEZE_SCHEMA!r}")
    if not isinstance(value["approved_by"], str) or not value["approved_by"].strip():
        raise ValueError("architecture freeze approved_by must be a non-empty string")

    package_root = value["package_root"]
    if not _confined_relative(package_root) or package_root.endswith("/"):
        raise ValueError(
            "architecture freeze package_root must be a relative path confined "
            "below the subject, with no trailing slash"
        )

    modules = value["modules"]
    if not isinstance(modules, dict) or not modules:
        raise ValueError(
            "architecture freeze modules must be a non-empty map of module name "
            "to path; a freeze about no modules decides nothing"
        )
    seen_paths: set[str] = set()
    for name, path in modules.items():
        if not isinstance(name, str) or _MODULE_NAME.fullmatch(name) is None:
            raise ValueError(
                f"architecture freeze module name {name!r} must be an identifier"
            )
        if not _confined_relative(path) or not (
            path == package_root or path.startswith(package_root + "/")
        ):
            raise ValueError(
                f"architecture freeze module {name!r} path {path!r} must be a "
                f"relative path under package_root {package_root!r}"
            )
        if path in seen_paths:
            raise ValueError(f"architecture freeze maps two modules to {path!r}")
        seen_paths.add(path)

    edges = value["allowed_edges"]
    if not isinstance(edges, list):
        raise ValueError("architecture freeze allowed_edges must be a list")
    names = set(modules)
    seen_edges: set[tuple[str, str]] = set()
    for edge in edges:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or not all(isinstance(end, str) for end in edge)
        ):
            raise ValueError(f"architecture freeze edge {edge!r} must be a name pair")
        if edge[0] not in names or edge[1] not in names:
            raise ValueError(
                f"architecture freeze edge {edge!r} names an undeclared module; "
                "an edge to a module the freeze does not carry is a hole, not a "
                "policy"
            )
        pair = (edge[0], edge[1])
        if pair in seen_edges:
            raise ValueError(f"architecture freeze declares edge {edge!r} twice")
        seen_edges.add(pair)
    if edges != sorted(edges):
        raise ValueError("architecture freeze allowed_edges must be sorted")
    return cast(ArchitectureFreeze, value)


def load_architecture_freeze_bytes(raw: bytes) -> dict[str, object]:
    """Parse exact canonical JSON freeze bytes already selected by a caller."""

    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse architecture freeze: {exc}") from exc
    freeze = validate_architecture_freeze(value)
    if raw != canonical_json_bytes(freeze):
        raise ValueError("architecture freeze must contain exact canonical JSON bytes")
    return cast(dict[str, object], freeze)


def architecture_freeze_digest(freeze: ArchitectureFreeze) -> str:
    """The digest a claim's argv pins: over the canonical freeze bytes."""

    validated = validate_architecture_freeze(dict(freeze))
    return "sha256:" + hashlib.sha256(canonical_json_bytes(validated)).hexdigest()


def freeze_digest_of_bytes(raw: bytes) -> str:
    """Parse freeze bytes and answer the digest of their canonical form."""

    return architecture_freeze_digest(
        cast(ArchitectureFreeze, load_architecture_freeze_bytes(raw))
    )


def _module_of(freeze: ArchitectureFreeze, relative: str) -> str | None:
    """The module a file belongs to: exact path, else the longest prefix."""

    best: tuple[int, str] | None = None
    for name, path in freeze["modules"].items():
        if relative == path:
            return name
        if relative.startswith(path + "/"):
            length = len(path)
            if best is None or length > best[0]:
                best = (length, name)
    return best[1] if best is not None else None


def _resolve_file(root: Path, parts: Sequence[str]) -> str | None:
    """The file a dotted path names under the freeze's package root."""

    base = "/".join(parts)
    for candidate in (f"{base}.py", f"{base}/__init__.py"):
        if (root / candidate).is_file():
            return candidate
    return None


def _line_bytes(lines: list[bytes], line: int) -> bytes:
    return lines[line - 1] if 1 <= line <= len(lines) else b""


def _line_text(lines: list[bytes], line: int) -> str:
    return _line_bytes(lines, line).decode("utf-8", errors="replace").rstrip("\n")


def _bound(rule_id: str, path: str, line: int, lines: list[bytes]) -> ArchFinding:
    return ArchFinding(
        rule_id=rule_id,
        path=path,
        line=line,
        snippet=_line_text(lines, line),
        fingerprint=fingerprint(rule_id, path, line, line, _line_bytes(lines, line)),
    )


def _absolute_parts(freeze: ArchitectureFreeze, dotted: str) -> list[str] | None:
    """Root-relative path parts for an absolute name inside the package.

    The package's dotted name is the last component of `package_root` — `pkg`
    for a flat layout, `ranex` for a src layout — and every part after it
    becomes a path below the root, so `_resolve_file` sees one shape.
    """

    package = freeze["package_root"].rsplit("/", 1)[-1]
    root_parts = freeze["package_root"].split("/")
    if dotted == package:
        return root_parts
    if dotted.startswith(package + "."):
        return [*root_parts, *dotted[len(package) + 1 :].split(".")]
    return None


def _relative_parts(
    freeze: ArchitectureFreeze, relative: str, level: int, module: str | None
) -> list[str] | None:
    """Parts for a relative import, or None when it escapes the frozen root.

    A module's and a package's level-1 anchor is the same thing — the file's
    containing directory — so no `__init__.py` special case exists here. The
    climb may not rise above `package_root`: an import that escapes the
    frozen root names something the freeze says nothing about.
    """

    anchor = relative.rsplit("/", 1)[0].split("/")
    floor = len(freeze["package_root"].split("/"))
    climb = level - 1
    if climb > len(anchor) - floor:
        return None
    if climb:
        anchor = anchor[: len(anchor) - climb]
    return [*anchor, *(module.split(".") if module else [])]


def _edges(
    root: Path,
    freeze: ArchitectureFreeze,
    relative: str,
    tree: ast.Module,
) -> list[tuple[int, str]]:
    """Every internal import edge in one file as `(line, target module)`."""

    targets: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            line, names, module, level = node.lineno, (
                alias.name for alias in node.names
            ), None, 0
        elif isinstance(node, ast.ImportFrom):
            line, names, module, level = (
                node.lineno,
                (alias.name for alias in node.names),
                node.module,
                node.level,
            )
        else:
            continue
        if level:
            base_parts = _relative_parts(freeze, relative, level, module)
        else:
            base_parts = (
                _absolute_parts(freeze, module) if module is not None else None
            )
        if base_parts is None:
            continue  # the import names something outside the frozen package
        files = [
            resolved
            for resolved in (
                _resolve_file(root, [*base_parts, name]) for name in names
            )
            if resolved is not None
        ]
        if not files:
            base_file = _resolve_file(root, base_parts)
            files = [base_file] if base_file is not None else []
        for file in files:
            target = _module_of(freeze, file)
            if target is not None:
                targets.append((line, target))
    return targets


def _walk(
    root: Path,
    freeze_bytes: bytes,
    freeze_relative: str,
    expected_digest: str | None,
) -> tuple[tuple[ArchFinding, ...], tuple[str, ...]]:
    """Every finding and every witnessed file, in deterministic order."""

    freeze = cast(
        ArchitectureFreeze, load_architecture_freeze_bytes(freeze_bytes)
    )
    package_root = freeze["package_root"]
    findings: list[ArchFinding] = []
    files: list[str] = []

    # The freeze file is witnessed whenever the scanner ran: it read the
    # file, and a scope that carries the freeze path must not read the
    # scanner's own input as missing.
    files.append(freeze_relative)
    if expected_digest is not None:
        # The tamper control: the freeze's canonical bytes must hash to the
        # digest the catalog pinned, so a weakened copy the subject carries
        # cannot quietly become the policy. The finding binds to the freeze
        # file's own bytes at the path the argv named, which puts it in the
        # frozen scope's universe — and the walk stops, because a freeze that
        # is not the approved one decides nothing worth reporting.
        if architecture_freeze_digest(freeze) != expected_digest:
            lines = freeze_bytes.splitlines(keepends=True)
            findings.append(
                ArchFinding(
                    rule_id=RULE_TAMPERED,
                    path=freeze_relative,
                    line=1,
                    snippet=_line_text(lines, 1),
                    fingerprint=fingerprint(
                        RULE_TAMPERED, freeze_relative, 1, 1, _line_bytes(lines, 1)
                    ),
                )
            )
            return (
                tuple(sorted(findings, key=lambda f: (f.path, f.line, f.rule_id))),
                tuple(files),
            )

    allowed = {tuple(edge) for edge in freeze["allowed_edges"]}
    undeclared: list[str] = []
    stack: list[str] = [package_root]
    while stack:
        directory = stack.pop()
        with os.scandir(root / directory) as entries:
            names = sorted(entry.name for entry in entries)
        directories: list[str] = []
        for name in names:
            relative = f"{directory}/{name}"
            entry_path = root / relative
            if entry_path.is_dir() and not entry_path.is_symlink():
                if name not in SKIPPED_DIRECTORIES:
                    directories.append(relative)
                continue
            if not name.endswith(".py"):
                continue
            raw = entry_path.read_bytes()
            files.append(relative)
            # A file the walk cannot parse is a scan that cannot complete:
            # raise, exit 2, no artifact, and absence blocks.
            tree = ast.parse(raw.decode("utf-8"), filename=relative)
            lines = raw.splitlines(keepends=True)
            source = _module_of(freeze, relative)
            if source is None:
                # No vertex in the approved graph: the freeze does not
                # describe this tree, and a finding on an out-of-scope path
                # is invisible to the frozen universe — so the scan refuses
                # instead of decorating, and admitting the module is a freeze
                # update, never an acceptance.
                undeclared.append(relative)
                continue
            for line, target in _edges(root, freeze, relative, tree):
                if (source, target) not in allowed:
                    findings.append(_bound(RULE_FORBIDDEN, relative, line, lines))
        stack.extend(sorted(directories, reverse=True))
    if undeclared:
        raise ValueError(
            "files under package_root in no freeze module: "
            + ", ".join(sorted(undeclared))
            + "; admit them through a freeze update, never an acceptance"
        )
    return (
        tuple(sorted(findings, key=lambda f: (f.path, f.line, f.rule_id))),
        tuple(files),
    )


def arch_sarif_bytes(
    root: Path,
    freeze_bytes: bytes,
    *,
    freeze_relative: str,
    expected_digest: str | None = None,
) -> bytes:
    """The SARIF 2.1.0 artifact for one scan of `root`, byte-deterministic."""

    findings, files = _walk(root, freeze_bytes, freeze_relative, expected_digest)

    def result(finding: ArchFinding) -> dict[str, object]:
        return {
            "ruleId": finding.rule_id,
            "level": "error",
            "message": {
                "text": {
                    RULE_FORBIDDEN: "an import edge the approved freeze does not list",
                    RULE_TAMPERED: "freeze bytes do not match the digest the "
                    "catalog pinned",
                }[finding.rule_id]
            },
            "fingerprints": {"ranex/v1": finding.fingerprint},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.path},
                        "region": {
                            "startLine": finding.line,
                            "endLine": finding.line,
                            "snippet": {"text": finding.snippet},
                        },
                    }
                }
            ],
        }

    document = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ranex-arch",
                        "informationUri": "https://github.com/anthonykewl20/ranex",
                        "rules": [
                            {
                                "id": rule_id,
                                "shortDescription": {"text": description},
                                "defaultConfiguration": {"level": level},
                            }
                            for rule_id, level, description in _RULES
                        ],
                    }
                },
                "invocations": [{"executionSuccessful": True}],
                "artifacts": [{"location": {"uri": name}} for name in files],
                "results": [result(finding) for finding in findings],
            }
        ],
    }
    return canonical_json_bytes(document)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranex.foundation.arch_scan",
        description="check import edges against an approved architecture freeze; "
        "emit SARIF 2.1.0",
    )
    subparsers = parser.add_subparsers(dest="verb", required=True)

    check = subparsers.add_parser("check", help="scan a tree and write the artifact")
    check.add_argument("--freeze", required=True, help="the committed freeze JSON")
    check.add_argument(
        "--expected-freeze-digest",
        default=None,
        help="sha256: over the freeze's canonical bytes, as the claim's argv pins "
        "it; a mismatch is a finding, never a silent policy change",
    )
    check.add_argument("--root", default=".", help="the tree to scan")
    check.add_argument("--output-format", choices=["sarif"], default="sarif")
    check.add_argument(
        "--output-file",
        required=True,
        help="where the SARIF artifact is written (the governed run binds a "
        "digest to it)",
    )

    digest = subparsers.add_parser(
        "digest", help="print the canonical-bytes digest a catalog should pin"
    )
    digest.add_argument("--freeze", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The installed entry point. Returns 0 however many findings it found."""

    arguments = _parser().parse_args(argv)
    if arguments.verb == "digest":
        try:
            raw = Path(arguments.freeze).read_bytes()
        except OSError as exc:
            print(f"ranex-arch: cannot read the freeze: {exc}", file=sys.stderr)
            return 2
        try:
            print(freeze_digest_of_bytes(raw))
            return 0
        except ValueError as exc:
            print(f"ranex-arch: cannot digest the freeze: {exc}", file=sys.stderr)
            return 2
    output = Path(arguments.output_file)
    try:
        freeze = Path(arguments.freeze)
        freeze_bytes = freeze.read_bytes()
        artifact = arch_sarif_bytes(
            Path(arguments.root),
            freeze_bytes,
            freeze_relative=freeze.as_posix(),
            expected_digest=arguments.expected_freeze_digest,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(output, artifact, root=output.absolute().parent)
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"ranex-arch: cannot complete the scan: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # the installed kernel's entry point, never a copy
    sys.exit(main())
