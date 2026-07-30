from __future__ import annotations

import ast
import importlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KERNEL_ROOT = PROJECT_ROOT / "src" / "ranex"
CONTEXT_EDGE_CONTRACT = (
    PROJECT_ROOT / "architecture" / "contracts" / "context-dependency-edges.json"
)

_LAYERS = frozenset({"api", "domain", "application", "adapters"})
_DOMAIN_FORBIDDEN_IMPORTS = frozenset(
    {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "random",
        "requests",
        "secrets",
        "sqlalchemy",
        "socket",
        "sqlite3",
        "subprocess",
        "time",
        "uuid",
        "yaml",
    }
)
_DOMAIN_FORBIDDEN_CALLS = frozenset(
    {
        "__import__",
        "datetime.now",
        "datetime.today",
        "datetime.utcnow",
        "importlib.import_module",
        "open",
        "os.getenv",
        "random.random",
        "random.randint",
        "secrets.token_hex",
        "time.time",
        "uuid.uuid1",
        "uuid.uuid4",
    }
)


@dataclass(frozen=True, order=True)
class ImportViolation:
    path: str
    line: int
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.detail}"


def _python_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root.parent).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _source_location(path: Path, root: Path) -> tuple[str, str | None]:
    relative = path.relative_to(root)
    context = relative.parts[0]
    layer = relative.parts[1] if len(relative.parts) > 1 else None
    return context, layer if layer in _LAYERS else None


def _imported_modules(
    tree: ast.AST,
    *,
    current_module: str | None = None,
    is_package: bool = False,
) -> tuple[tuple[str, int], ...]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_import_from(
                node,
                current_module=current_module,
                is_package=is_package,
            )
            if module:
                imports.append((module, node.lineno))
    return tuple(imports)


def _resolve_import_from(
    node: ast.ImportFrom,
    *,
    current_module: str | None,
    is_package: bool,
) -> str | None:
    if node.level == 0:
        return node.module
    if current_module is None:
        return node.module
    package_parts = current_module.split(".")
    if not is_package:
        package_parts = package_parts[:-1]
    ascend = node.level - 1
    if ascend > len(package_parts):
        return node.module
    base_parts = package_parts[: len(package_parts) - ascend]
    if node.module:
        base_parts.extend(node.module.split("."))
    return ".".join(base_parts)


def _call_name(call: ast.Call) -> str | None:
    parts: list[str] = []
    current: ast.expr = call.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _dynamic_imports(tree: ast.AST) -> tuple[tuple[str, int], ...]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in {"__import__", "import_module", "importlib.import_module"}:
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            module = node.args[0].value
            if isinstance(module, str):
                imports.append((module, node.lineno))
    return tuple(imports)


def _is_hermes_module(module: str) -> bool:
    return any(
        part == "hermes" or part.startswith("hermes_") for part in module.split(".")
    )


def _is_allowed_same_context_import(
    source_layer: str | None,
    target_layer: str | None,
) -> bool:
    if source_layer == "domain":
        return target_layer == "domain"
    if source_layer == "application":
        return target_layer in {"domain", "application"}
    if source_layer == "api":
        return target_layer in {"api", "domain", "application"}
    if source_layer == "adapters":
        return target_layer in {"api", "domain", "application"}
    return target_layer is None


def collect_import_violations(root: Path = KERNEL_ROOT) -> tuple[ImportViolation, ...]:
    violations: list[ImportViolation] = []
    declared_edges = (
        _declared_context_edges() if root.resolve() == KERNEL_ROOT.resolve() else None
    )
    for path in _python_files(root):
        relative_path = path.relative_to(
            PROJECT_ROOT if path.is_relative_to(PROJECT_ROOT) else root
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        source_context, source_layer = _source_location(path, root)
        source_module = _module_name(path, root)

        for module, line in _dynamic_imports(tree):
            if _is_hermes_module(module):
                violations.append(
                    ImportViolation(
                        str(relative_path),
                        line,
                        "NO_HERMES_IMPORT",
                        f"kernel dynamically imports {module!r}",
                    )
                )

        for module, line in _imported_modules(
            tree,
            current_module=source_module,
            is_package=path.name == "__init__.py",
        ):
            if _is_hermes_module(module):
                violations.append(
                    ImportViolation(
                        str(relative_path),
                        line,
                        "NO_HERMES_IMPORT",
                        f"kernel imports {module!r}",
                    )
                )

            root_module = module.split(".", maxsplit=1)[0]
            if (
                source_context == "foundation"
                and root_module not in sys.stdlib_module_names
            ):
                violations.append(
                    ImportViolation(
                        str(relative_path),
                        line,
                        "FOUNDATION_STDLIB_ONLY",
                        f"foundation imports {module!r}",
                    )
                )

            if source_layer == "domain":
                if root_module in _DOMAIN_FORBIDDEN_IMPORTS:
                    violations.append(
                        ImportViolation(
                            str(relative_path),
                            line,
                            "PURE_DOMAIN_DEPENDENCY",
                            f"domain imports effect/framework module {module!r}",
                        )
                    )
                elif root_module not in {"ranex", *sys.stdlib_module_names}:
                    violations.append(
                        ImportViolation(
                            str(relative_path),
                            line,
                            "PURE_DOMAIN_DEPENDENCY",
                            f"domain imports third-party module {module!r}",
                        )
                    )

            parts = module.split(".")
            if len(parts) < 2 or parts[0] != "ranex":
                continue
            target_context = parts[1]
            target_layer = parts[2] if len(parts) > 2 and parts[2] in _LAYERS else None

            if source_context == "foundation":
                violations.append(
                    ImportViolation(
                        str(relative_path),
                        line,
                        "FOUNDATION_INDEPENDENCE",
                        f"foundation imports kernel module {module!r}",
                    )
                )
                continue

            if target_context == "foundation":
                continue
            if target_context != source_context:
                if target_layer != "api":
                    violations.append(
                        ImportViolation(
                            str(relative_path),
                            line,
                            "CROSS_CONTEXT_PUBLIC_API_ONLY",
                            f"{source_context!r} imports private module {module!r}",
                        )
                    )
                elif (
                    declared_edges is not None
                    and (source_context, target_context) not in declared_edges
                ):
                    violations.append(
                        ImportViolation(
                            str(relative_path),
                            line,
                            "DECLARED_CONTEXT_EDGE_REQUIRED",
                            (
                                f"{source_context!r} -> {target_context!r} "
                                "is not registered"
                            ),
                        )
                    )
                continue
            if not _is_allowed_same_context_import(source_layer, target_layer):
                violations.append(
                    ImportViolation(
                        str(relative_path),
                        line,
                        "INWARD_DEPENDENCY_ONLY",
                        f"{source_layer!r} imports {target_layer!r} via {module!r}",
                    )
                )

        if source_layer == "domain":
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and (name := _call_name(node))
                    and name in _DOMAIN_FORBIDDEN_CALLS
                ):
                    violations.append(
                        ImportViolation(
                            str(relative_path),
                            node.lineno,
                            "PURE_DOMAIN_CALL",
                            f"domain calls nondeterministic/effectful {name!r}",
                        )
                    )

    return tuple(sorted(violations))


def _declared_context_edges() -> frozenset[tuple[str, str]]:
    contract = json.loads(CONTEXT_EDGE_CONTRACT.read_text(encoding="utf-8"))
    return frozenset(
        (entry["caller"], entry["callee"]) for entry in contract["entries"]
    )


def collect_module_cycles(root: Path = KERNEL_ROOT) -> tuple[tuple[str, ...], ...]:
    files = {_module_name(path, root): path for path in _python_files(root)}
    graph: dict[str, set[str]] = defaultdict(set)
    for module, path in files.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported, _line in _imported_modules(
            tree,
            current_module=module,
            is_package=path.name == "__init__.py",
        ):
            if imported in files:
                graph[module].add(imported)

    cycles: set[tuple[str, ...]] = set()
    active: list[str] = []
    active_set: set[str] = set()
    complete: set[str] = set()

    def visit(module: str) -> None:
        if module in active_set:
            start = active.index(module)
            cycle = [*active[start:], module]
            rotations = [
                tuple(cycle[index:-1] + cycle[: index + 1])
                for index in range(len(cycle) - 1)
            ]
            cycles.add(min(rotations))
            return
        if module in complete:
            return
        active.append(module)
        active_set.add(module)
        for target in sorted(graph[module]):
            visit(target)
        active.pop()
        active_set.remove(module)
        complete.add(module)

    for module in sorted(files):
        visit(module)
    return tuple(sorted(cycles))


def _format_violations(violations: tuple[ImportViolation, ...]) -> str:
    return "\n".join(str(violation) for violation in violations)


def test_kernel_imports_follow_layering_and_have_no_hermes_reachability() -> None:
    violations = collect_import_violations()
    assert not violations, _format_violations(violations)


def test_kernel_import_graph_is_acyclic() -> None:
    cycles = collect_module_cycles()
    assert not cycles, "\n".join(" -> ".join(cycle) for cycle in cycles)


def test_checker_rejects_private_cross_context_import(tmp_path: Path) -> None:
    root = tmp_path / "ranex"
    source = root / "governed_execution" / "application" / "bad.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from ranex.assurance.domain.evidence import Evidence\n",
        encoding="utf-8",
    )

    violations = collect_import_violations(root)

    assert any(
        violation.rule == "CROSS_CONTEXT_PUBLIC_API_ONLY" for violation in violations
    )


def test_checker_rejects_relative_private_cross_context_import(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ranex"
    source = root / "governed_execution" / "application" / "bad.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from ...assurance.domain.evidence import Evidence\n",
        encoding="utf-8",
    )

    violations = collect_import_violations(root)

    assert any(
        violation.rule == "CROSS_CONTEXT_PUBLIC_API_ONLY" for violation in violations
    )


def test_checker_rejects_hermes_import(tmp_path: Path) -> None:
    root = tmp_path / "ranex"
    source = root / "governed_execution" / "application" / "bad.py"
    source.parent.mkdir(parents=True)
    source.write_text("import hermes_agent\n", encoding="utf-8")

    violations = collect_import_violations(root)

    assert any(violation.rule == "NO_HERMES_IMPORT" for violation in violations)


def test_checker_rejects_dynamic_hermes_import(tmp_path: Path) -> None:
    root = tmp_path / "ranex"
    source = root / "governed_execution" / "application" / "bad.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "import importlib\nimportlib.import_module('hermes_agent.core')\n",
        encoding="utf-8",
    )

    violations = collect_import_violations(root)

    assert any(violation.rule == "NO_HERMES_IMPORT" for violation in violations)


def test_checker_rejects_domain_environment_dependency(tmp_path: Path) -> None:
    root = tmp_path / "ranex"
    source = root / "governed_execution" / "domain" / "bad.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "import os\nTOKEN = os.environ['TOKEN']\n",
        encoding="utf-8",
    )

    violations = collect_import_violations(root)

    assert any(violation.rule == "PURE_DOMAIN_DEPENDENCY" for violation in violations)


def test_checker_allows_api_to_expose_immutable_domain_types(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ranex"
    source = root / "assurance" / "api" / "contracts.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from ranex.assurance.domain.gates import GateEvaluation\n",
        encoding="utf-8",
    )

    assert collect_import_violations(root) == ()


def test_importing_entire_kernel_graph_loads_no_hermes_dependency() -> None:
    for path in _python_files(KERNEL_ROOT):
        importlib.import_module(_module_name(path, KERNEL_ROOT))

    loaded_hermes_modules = tuple(
        sorted(module for module in sys.modules if _is_hermes_module(module))
    )
    assert loaded_hermes_modules == ()
