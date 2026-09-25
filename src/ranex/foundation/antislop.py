"""The C3 anti-slop scanner: a test-integrity census, SARIF out.

An agent that cannot make a test pass can still make it stop asserting:
delete the body, replace the check with a constant truth, comment one
assertion out, regenerate the snapshot, narrow the generated inputs. The
suite stays green and lies. This scanner is the deterministic counterweight
the kernel-oracle science run measured (§3.3: 3/3 plants blocked, 0/6
known-good false-positives; the two further plants are adopted as behaviour
from oracle-gate's AI-test-weakening enumeration, CC-BY-4.0, methodology
only). Pure `ast` — no model, no network, no judgment; `evaluate()` and the
envelope learn nothing (ADR-060 seam B).

What it emits, all through the #97 fingerprint so regions bind to the
subject's bytes:

  ranex/antislop-tautology          `error`  an assert whose truth is a
                                             constant (`assert True`,
                                             `assert not False`)
  ranex/antislop-pass-body          `error`  a test whose body is `pass`/`...`
  ranex/antislop-snapshot-blind-update  `error`  a snapshot-update flag or
                                             `update=True` kwarg — the
                                             assertion regenerated to agree
  ranex/antislop-input-range-narrowing `error`  `max_examples` below the
                                             floor, or a point input range
  ranex/antislop-census             `none`   one per test: its effective
                                             assert count

The census is the frozen expectations' raw material: `antislop_results`
reduces the artifact against the approved tree's per-test counts, so an
assertion quietly deleted becomes `0 < frozen` — and a test removed from
the census entirely is `missing`, which blocks. A test with no `assert`
statement but a real body (`pytest.raises`, `self.assertEqual`) counts: the
science run's own detector bug, fixed before shipping rather than after.

Like markers, the scanner exits 0 however many findings it reports and
decides through its artifact, and runs as the installed kernel's entry
point — never a script the observed tree carries.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import fingerprint

RULE_TAUTOLOGY = "ranex/antislop-tautology"
RULE_PASS_BODY = "ranex/antislop-pass-body"
RULE_SNAPSHOT_BLIND = "ranex/antislop-snapshot-blind-update"
RULE_RANGE_NARROW = "ranex/antislop-input-range-narrowing"
RULE_CENSUS = "ranex/antislop-census"

#: The exclusion set markers made deterministic, unchanged here: the same
#: names, on every subject, whatever the language.
SKIPPED_DIRECTORIES = frozenset(
    {".git", "node_modules", "build", "dist", "target", "__pycache__"}
)

#: Snapshot-update flags of the syrupy/syrupy-jest family: the argv shapes a
#: test or its harness uses to regenerate the very snapshot it asserts on.
SNAPSHOT_UPDATE_FLAGS = ("--snapshot-update", "--update-snapshots")

#: hypothesis's default sample is 100 examples; a property test that runs
#: fewer than this is not probing. The floor is a reviewed constant, not a
#: measurement — an honest smaller sample names its ceiling with a marker.
MIN_EXAMPLES_FLOOR = 10

_RULES = (
    (RULE_TAUTOLOGY, "error", "an assertion whose truth is a constant"),
    (RULE_PASS_BODY, "error", "a test whose body is pass or ellipsis"),
    (
        RULE_SNAPSHOT_BLIND,
        "error",
        "a snapshot blindly updated rather than asserted on",
    ),
    (
        RULE_RANGE_NARROW,
        "error",
        "a generated-input range narrowed below a probing sample",
    ),
    (RULE_CENSUS, "none", "one per test: its effective assert count"),
)


@dataclass(frozen=True, slots=True)
class AntislopFinding:
    """One structural finding, bound to the subject's bytes."""

    rule_id: str
    path: str
    line: int
    snippet: str
    fingerprint: str
    #: the ID the finding fails first: the carrying test, or the file when
    #: the finding is module-scoped (a snapshot flag outside any test).
    named: str

    @property
    def level(self) -> str:
        return "error"

    @property
    def finding_id(self) -> str:
        return f"{self.path}::{self.rule_id}::{self.fingerprint}"


@dataclass(frozen=True, slots=True)
class TestCensus:
    """One observed test: its ID and its effective assert count."""

    test_id: str
    count: int
    line: int
    snippet: str
    fingerprint: str


def _is_test_file(name: str) -> bool:
    return name.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py")
    )


def _called_name(expression: ast.expr) -> str | None:
    """The name a call is made by: the attribute segment, or the bare name."""

    if isinstance(expression, ast.Attribute):
        return expression.attr
    if isinstance(expression, ast.Name):
        return expression.id
    return None


def _effective_asserts(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """What the freeze records: asserts plus assertion-equivalent calls.

    `pytest.raises` and unittest's `assert*` methods assert as surely as the
    keyword does; counting the keyword alone turned real assertion-free
    tests into known-good false-positives in the science run.
    """

    count = 0
    for node in ast.walk(function):
        if isinstance(node, ast.Assert):
            count += 1
        elif isinstance(node, ast.Call):
            name = _called_name(node.func)
            if name == "raises" or (name is not None and name.startswith("assert")):
                count += 1
    return count


def _always_true(expression: ast.expr) -> bool:
    if isinstance(expression, ast.Constant):
        return bool(expression.value)
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        return isinstance(expression.operand, ast.Constant) and not bool(
            expression.operand.value
        )
    return False


def _is_pass_only(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(function.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # a docstring is documentation, not assertion
    if not body:
        return False

    def inert(statement: ast.stmt) -> bool:
        if isinstance(statement, ast.Pass):
            return True
        return (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and statement.value.value is Ellipsis
        )

    return all(inert(statement) for statement in body)


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _constant_int(expression: ast.expr | None) -> int | None:
    if (
        isinstance(expression, ast.Constant)
        and isinstance(expression.value, int)
        and not isinstance(expression.value, bool)
    ):
        return expression.value
    return None


def _point_range(call: ast.Call) -> bool:
    """A generated integer range of exactly one value, however spelled."""

    keyword_bounds = (
        _constant_int(_keyword(call, "min_value")),
        _constant_int(_keyword(call, "max_value")),
    )
    positional_bounds: tuple[int | None, int | None] = (None, None)
    if len(call.args) >= 2:
        positional_bounds = (
            _constant_int(call.args[0]),
            _constant_int(call.args[1]),
        )
    return any(
        low is not None and high is not None and low == high
        for low, high in (keyword_bounds, positional_bounds)
    )


def _module_findings(
    relative: str, tree: ast.Module, lines: list[bytes]
) -> list[AntislopFinding]:
    """Module-scoped plants: snapshot flags and narrowed generated inputs."""

    seen: dict[tuple[str, int], None] = {}
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 1)
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and any(flag in node.value for flag in SNAPSHOT_UPDATE_FLAGS)
        ):
            seen.setdefault((RULE_SNAPSHOT_BLIND, line))
        elif isinstance(node, ast.Call):
            name = _called_name(node.func) or ""
            if "snapshot" in name.lower():
                update = _keyword(node, "update")
                if isinstance(update, ast.Constant) and update.value is True:
                    seen.setdefault((RULE_SNAPSHOT_BLIND, line))
            examples = _constant_int(_keyword(node, "max_examples"))
            if examples is not None and examples < MIN_EXAMPLES_FLOOR:
                seen.setdefault((RULE_RANGE_NARROW, line))
            elif name == "integers" and _point_range(node):
                seen.setdefault((RULE_RANGE_NARROW, line))
    return [
        AntislopFinding(
            rule_id=rule_id,
            path=relative,
            line=line,
            snippet=_line_text(lines, line),
            fingerprint=fingerprint(
                rule_id, relative, line, line, _line_bytes(lines, line)
            ),
            named=relative,
        )
        for rule_id, line in seen
    ]


def _line_bytes(lines: list[bytes], line: int) -> bytes:
    return lines[line - 1] if 1 <= line <= len(lines) else b""


def _line_text(lines: list[bytes], line: int) -> str:
    return _line_bytes(lines, line).decode("utf-8", errors="replace").rstrip("\n")


def _test_functions(
    tree: ast.Module,
) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]]:
    """Every test function with its frozen-universe ID: class-qualified."""

    found: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]] = []
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ):
            found.append((node, node.name))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child.name.startswith("test_")
                ):
                    found.append((child, f"{node.name}::{child.name}"))
    return found


def _scan_file(
    relative: str, raw: bytes
) -> tuple[list[AntislopFinding], list[TestCensus]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], []  # binary by the only test grep needs
    tree = ast.parse(text, filename=relative)
    lines = raw.splitlines(keepends=True)

    findings = _module_findings(relative, tree, lines)
    census: list[TestCensus] = []
    for function, name in _test_functions(tree):
        test_id = f"{relative}::{name}"
        census.append(
            TestCensus(
                test_id=test_id,
                count=_effective_asserts(function),
                line=function.lineno,
                snippet=_line_text(lines, function.lineno),
                fingerprint=fingerprint(
                    RULE_CENSUS,
                    relative,
                    function.lineno,
                    function.lineno,
                    _line_bytes(lines, function.lineno),
                ),
            )
        )
        if _is_pass_only(function):
            findings.append(
                _bound(RULE_PASS_BODY, relative, function.lineno, lines, test_id)
            )
        for node in ast.walk(function):
            if isinstance(node, ast.Assert) and _always_true(node.test):
                findings.append(
                    _bound(RULE_TAUTOLOGY, relative, node.lineno, lines, test_id)
                )
    return findings, census


def _bound(
    rule_id: str, relative: str, line: int, lines: list[bytes], named: str
) -> AntislopFinding:
    return AntislopFinding(
        rule_id=rule_id,
        path=relative,
        line=line,
        snippet=_line_text(lines, line),
        fingerprint=fingerprint(
            rule_id, relative, line, line, _line_bytes(lines, line)
        ),
        named=named,
    )


def _walk(
    root: Path,
) -> tuple[tuple[str, ...], tuple[AntislopFinding, ...], tuple[TestCensus, ...]]:
    """Every test file, finding and census entry, all in deterministic order."""

    files: list[str] = []
    findings: list[AntislopFinding] = []
    census: list[TestCensus] = []
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
            if not _is_test_file(name):
                continue
            file_findings, file_census = _scan_file(relative, entry_path.read_bytes())
            files.append(relative)
            findings.extend(file_findings)
            census.extend(file_census)
        stack.extend(sorted(directories, reverse=True))
    return (
        tuple(files),
        tuple(sorted(findings, key=lambda f: (f.path, f.line, f.rule_id))),
        tuple(sorted(census, key=lambda c: c.test_id)),
    )


def scanned_test_files(root: Path) -> tuple[str, ...]:
    """Every test file the walk reaches, as subject-relative paths."""

    return _walk(root)[0]


def scan_tree(root: Path) -> tuple[AntislopFinding, ...]:
    """Every structural finding, ordered by path, line, rule."""

    return _walk(root)[1]


def census_of_tree(root: Path) -> tuple[TestCensus, ...]:
    """Every observed test with its effective assert count, by ID order."""

    return _walk(root)[2]


def antislop_sarif_bytes(root: Path) -> bytes:
    """The SARIF 2.1.0 artifact for one scan of `root`, byte-deterministic."""

    files, findings, census = _walk(root)

    def result(
        rule_id: str, level: str, message: str, path: str, line: int, snippet: str, digest: str
    ) -> dict[str, object]:
        return {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": message},
            "fingerprints": {"ranex/v1": digest},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": path},
                        "region": {
                            "startLine": line,
                            "endLine": line,
                            "snippet": {"text": snippet},
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
                        "name": "ranex-antislop",
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
                    *(
                        result(
                            finding.rule_id,
                            finding.level,
                            finding.named,
                            finding.path,
                            finding.line,
                            finding.snippet,
                            finding.fingerprint,
                        )
                        for finding in findings
                    ),
                    *(
                        result(
                            RULE_CENSUS,
                            "none",
                            f"{entry.test_id} effective_asserts={entry.count}",
                            entry.test_id.split("::")[0],
                            entry.line,
                            entry.snippet,
                            entry.fingerprint,
                        )
                        for entry in census
                    ),
                ],
            }
        ],
    }
    return canonical_json_bytes(document)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranex.foundation.antislop",
        description="census test assertions and grep anti-slop shapes; emit SARIF 2.1.0",
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
        artifact = antislop_sarif_bytes(Path(arguments.root))
        output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(output, artifact, root=output.absolute().parent)
    except (OSError, SyntaxError) as exc:
        print(f"ranex-antislop: cannot complete the scan: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # the installed kernel's entry point, never a copy
    sys.exit(main())
