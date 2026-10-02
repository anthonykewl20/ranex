"""Ratchet configuration literals until centralized-settings migrations remove them."""

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tests/contract/fixtures/settings_literal_ratchet.json"
EXCLUDED = {
    "src/ranex/foundation/settings.py",
    "src/ranex/foundation/platform.py",
    "src/ranex/governed_execution/domain/verdict.py",
}
PATTERNS = {
    "host-path": re.compile(r"^/(usr|lib|lib32|lib64|bin|sbin|etc|opt|proc|sys|run|var|tmp|dev)(/|$)"),
    "url": re.compile(r"^[a-z][a-z0-9+.-]*://"),
    "governance-path": re.compile(r"^governance/"),
}


def scan_literals(root: Path) -> dict[str, dict[str, int]]:
    counts = {}
    for path in sorted((root / "src").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative in EXCLUDED:
            continue
        tree = ast.parse(path.read_text(), filename=relative)
        docstrings = set()
        env_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body and isinstance(node.body[0], ast.Expr):
                    value = node.body[0].value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        docstrings.add(value)
            if isinstance(node, ast.Call) and node.args:
                if ast.unparse(node.func) in {"os.environ.get", "os.getenv"}:
                    env_names.add(node.args[0])
            if isinstance(node, ast.Subscript) and ast.unparse(node.value) == "os.environ":
                env_names.add(node.slice)
        found = Counter()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or node in docstrings:
                continue
            for kind, pattern in PATTERNS.items():
                if pattern.match(node.value):
                    found[kind] += 1
            if node in env_names:
                found["env-name"] += 1
        if found:
            counts[relative] = dict(found)
    return counts


def differences(*, excess: bool) -> list[str]:
    found = scan_literals(ROOT)
    baseline = json.loads(BASELINE.read_text())
    failures = []
    for file in sorted(found.keys() | baseline.keys()):
        for kind in sorted(found.get(file, {}).keys() | baseline.get(file, {}).keys()):
            actual = found.get(file, {}).get(kind, 0)
            allowed = baseline.get(file, {}).get(kind, 0)
            if (actual > allowed) if excess else (actual < allowed):
                failures.append(f"{file} kind={kind} found={actual} allowed={allowed}")
    return failures


def test_no_count_exceeds_baseline():
    failures = differences(excess=True)
    assert not failures, "Configuration literal creep:\n" + "\n".join(failures)


def test_baseline_is_tight():
    failures = differences(excess=False)
    assert not failures, "Lower the baseline in the same commit:\n" + "\n".join(failures)


def test_excluded_files_are_not_scanned(tmp_path):
    for relative in EXCLUDED:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('X = "/usr/x"\n')
    assert scan_literals(tmp_path) == {}


def test_each_kind_is_detected(tmp_path):
    path = tmp_path / "src/example.py"
    path.parent.mkdir()
    path.write_text('"""/usr/x"""\nimport os\nX = "/etc/x"\nY = "https://example.test"\nZ = "governance/x"\nE = os.getenv("EXAMPLE")\n')
    assert scan_literals(tmp_path) == {
        "src/example.py": {"host-path": 1, "url": 1, "governance-path": 1, "env-name": 1}
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["--write-baseline"]:
        raise SystemExit("usage: test_settings_literal_ratchet.py --write-baseline")
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(scan_literals(ROOT), indent=2, sort_keys=True) + "\n")
