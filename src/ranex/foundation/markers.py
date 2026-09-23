"""The deliberate-shortcut scanner: a cut corner may be taken, not hidden.

A simplification that cuts a real corner leaves a `ranex:` comment naming two
things — the ceiling it accepts and the trigger that should revisit it:

    # ranex: global lock; per-account locks if throughput matters

Upstream (`DietrichGebert/ponytail`, MIT; adopted as behaviour per MAP §15.3,
no code vendored) harvests these with a model and tags the rotting form
`no-trigger, those rot silently`. Here the harvest is grep: this module is
stdlib-only, reads the tree it is pointed at, and emits SARIF 2.1.0 that
`scan_results` reduces exactly as it reduces ruff's. No model, no network, no
judgment anywhere near a verdict; `evaluate()` learns nothing.

What the form decides (#110):

    ranex: <ceiling>; <trigger>

  * no `;` — a ceiling with no revisit condition, the rotting marker — is
    `ranex/marker-no-trigger` at `error`;
  * an empty half is `ranex/marker-malformed` at `error`;
  * a well-formed marker is `ranex/marker-shortcut` at `note`: a measurement,
    not a gate. The gate rule is that a shortcut may be taken but may not be
    silent.

A marker inside a string literal is not a comment. Line-level quote tracking
decides: if the `#`/`//` prefix sits inside an unclosed quoted span that
opened earlier on the same line, the line is data, not a comment. A marker
inside a multi-line literal whose opening quotes sit on an earlier line is a
recorded residual of line-level tracking, not a promise.

The scanner runs as an installed entry point (`python -P -m
ranex.foundation.markers`), never as a script the observed tree carries
(#110 Correction 2), and exits 0 however many findings it reports: like
ruff's `--exit-zero`, it decides through its artifact, because a bound
`accepted` must stay reachable through a zero exit.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import fingerprint

RULE_SHORTCUT = "ranex/marker-shortcut"
RULE_NO_TRIGGER = "ranex/marker-no-trigger"
RULE_MALFORMED = "ranex/marker-malformed"

#: `(#|//) ?ranex:` — the comment prefixes of the languages upstream greps,
#: and no others: `/*` block comments are not line comments anywhere.
MARKER = b"ranex:"

#: Upstream's exclusion set (`node_modules/.git/build output`), made
#: deterministic: the same names, on every subject, whatever the language.
SKIPPED_DIRECTORIES = frozenset(
    {".git", "node_modules", "build", "dist", "target", "__pycache__"}
)

_RULES = (
    (RULE_SHORTCUT, "note", "a deliberate shortcut, ceiling and trigger named"),
    (RULE_NO_TRIGGER, "error", "a marker that names no trigger to revisit it"),
    (RULE_MALFORMED, "error", "a marker whose ceiling or trigger half is empty"),
)


@dataclass(frozen=True, slots=True)
class MarkerFinding:
    """One marker line, classified and bound to the subject's bytes."""

    rule_id: str
    level: str
    path: str
    line: int
    snippet: str
    fingerprint: str

    @property
    def finding_id(self) -> str:
        return f"{self.path}::{self.rule_id}::{self.fingerprint}"


def _comment_marker(line: bytes) -> int | None:
    """The offset of a `ranex:` marker's comment prefix, or None.

    A prefix inside a quoted span is a string literal, not a comment: the
    false-positive control (arm 6) exists to keep documentation quoting the
    convention from being refused as a violation. Both quote characters close
    strings, because the scanner is language-agnostic; a backslash escapes
    the next character, which is the convention of every mainstream grammar
    that has these quotes.
    """

    quote: bytes | None = None
    escaped = False
    index = 0
    while index < len(line) - len(MARKER):
        char = line[index : index + 1]
        if escaped:
            escaped = False
        elif char == b"\\" and quote is not None:
            escaped = True
        elif quote is not None:
            if char == quote:
                quote = None
        elif char in (b'"', b"'"):
            quote = char
        elif char == b"#":
            rest = line[index + 1 : index + 8]
            if rest.startswith(b"ranex:") or rest.startswith(b" ranex:"):
                return index
        elif char == b"/":
            if line[index + 1 : index + 2] == b"/":
                rest = line[index + 2 : index + 9]
                if rest.startswith(b"ranex:") or rest.startswith(b" ranex:"):
                    return index
                # A comment that does not carry the marker ends the line for
                # grep purposes: nothing after `//` can open a string.
                return None
        index += 1
    return None


def _classify(payload: str) -> tuple[str, str, str]:
    """`(rule_id, level, message)` for everything after `ranex:`."""

    ceiling, separator, trigger = payload.partition(";")
    if not separator:
        return (
            RULE_NO_TRIGGER,
            "error",
            "the marker names a ceiling but no trigger to revisit it; a shortcut "
            "without an expiry condition rots silently",
        )
    if not ceiling.strip() or not trigger.strip():
        return (
            RULE_MALFORMED,
            "error",
            "the marker's ceiling and trigger must both be non-empty; a half-empty "
            "marker names neither limit nor condition",
        )
    return (
        RULE_SHORTCUT,
        "note",
        f"deliberate shortcut — ceiling: {ceiling.strip()}; trigger: {trigger.strip()}",
    )


def _scan_bytes(relative: str, raw: bytes) -> list[MarkerFinding]:
    findings: list[MarkerFinding] = []
    for number, line in enumerate(raw.splitlines(keepends=True), start=1):
        offset = _comment_marker(line)
        if offset is None:
            continue
        snippet = line.rstrip(b"\n").decode("utf-8", errors="replace")
        # Located from the comment prefix, never from the snippet's start: a
        # string earlier on the line may quote the convention before the real
        # comment carries it.
        payload = snippet.find("ranex:", offset)
        assert payload != -1
        rule_id, level, _message = _classify(snippet[payload + len("ranex:") :])
        findings.append(
            MarkerFinding(
                rule_id=rule_id,
                level=level,
                path=relative,
                line=number,
                snippet=snippet,
                fingerprint=fingerprint(rule_id, relative, number, number, line),
            )
        )
    return findings


def _walk(root: Path) -> tuple[tuple[str, ...], tuple[MarkerFinding, ...]]:
    """Every scanned file and every finding, both in deterministic order."""

    files: list[str] = []
    findings: list[MarkerFinding] = []
    stack: list[str] = [""]
    while stack:
        directory = stack.pop()
        with os.scandir(root / directory) as entries:
            names = sorted(entry.name for entry in entries)
        directories: list[str] = []
        for name in names:
            relative = f"{directory}/{name}" if directory else name
            entry_path = root / relative
            if entry_path.is_dir() and not entry_path.is_symlink():
                if name not in SKIPPED_DIRECTORIES:
                    directories.append(relative)
                continue
            raw = entry_path.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                continue  # binary, by the only test grep needs
            files.append(relative)
            findings.extend(_scan_bytes(relative, raw))
        stack.extend(sorted(directories, reverse=True))
    return tuple(files), tuple(findings)


def scanned_files(root: Path) -> tuple[str, ...]:
    """Every file the walk reaches, as subject-relative paths."""

    return _walk(root)[0]


def scan_tree(root: Path) -> tuple[MarkerFinding, ...]:
    """Every marker finding, ordered by path then line."""

    return tuple(sorted(_walk(root)[1], key=lambda f: (f.path, f.line)))


def marker_sarif_bytes(root: Path) -> bytes:
    """The SARIF 2.1.0 artifact for one scan of `root`, byte-deterministic."""

    files, findings = _walk(root)
    document = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ranex-markers",
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
                "results": [
                    {
                        "ruleId": finding.rule_id,
                        "level": finding.level,
                        "message": {"text": f"{finding.path}:{finding.line}"},
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
                    for finding in findings
                ],
            }
        ],
    }
    return canonical_json_bytes(document)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranex.foundation.markers",
        description="grep deliberate-shortcut markers and emit SARIF 2.1.0",
    )
    parser.add_argument("--output-format", choices=["sarif"], default="sarif")
    parser.add_argument(
        "--output-file",
        required=True,
        help="where the SARIF artifact is written (the governed run binds a digest to it)",
    )
    parser.add_argument(
        "--root", default=".", help="the tree to scan (the claim runs in the subject)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The installed entry point. Returns 0 however many findings it found."""

    arguments = _parser().parse_args(argv)
    output = Path(arguments.output_file)
    try:
        artifact = marker_sarif_bytes(Path(arguments.root))
        output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(output, artifact, root=output.absolute().parent)
    except OSError as exc:
        print(f"ranex-markers: cannot write the scan: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # the installed kernel's entry point, never a copy
    sys.exit(main())
