"""SLICE-007 §2: the harness refuses to start without its bridge.

The wall argument: a harness that can start ungoverned is the hole; the gate
refuses before any loop, model call, or command dispatch.

SLICE-008 §11: the harness is Ranex. The rebrand is measured by driving the
command a person would type — `bin/ranex` — and reading what it prints, never
by grepping the tree for leftover strings.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _harness_dir() -> Path:
    default = Path(__file__).resolve().parents[2].parent / "ranex-harness"
    return Path(os.environ.get("RANEX_HARNESS_DIR", default))


@pytest.fixture(scope="module")
def harness() -> Path:
    tree = _harness_dir()
    if not (tree / "package.json").is_file():
        pytest.skip(f"harness fork not present at {tree} (set RANEX_HARNESS_DIR)")
    return tree


@pytest.fixture(scope="module")
def bun() -> Path:
    executable = Path.home() / ".bun" / "bin" / "bun"
    if not executable.is_file():
        pytest.skip("bun toolchain not installed at ~/.bun/bin/bun")
    return executable


def _environment(bun: Path, **binding: str) -> dict[str, str]:
    """Give the fork only its runtime path, home, and explicit bridge values."""

    env = {
        "PATH": f"{bun.parent}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "HOME": str(Path.home()),
    }
    env.update(binding)
    return env


def _invoke(
    harness: Path, bun: Path, *args: str, **binding: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(bun), "run", "--cwd", "packages/ranex", "src/index.ts", *args],
        cwd=harness,
        capture_output=True,
        text=True,
        timeout=120,
        env=_environment(bun, **binding),
        check=False,
    )


def _assert_unbridged(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0, "unbridged startup must fail closed"
    assert "RANEX" in result.stderr
    assert "unbridged" in result.stderr.lower()


def test_version_refuses_without_binding(harness: Path, bun: Path) -> None:
    """Even the harmless version command cannot start ungoverned."""

    _assert_unbridged(_invoke(harness, bun, "--version"))


def test_run_help_refuses_without_binding(harness: Path, bun: Path) -> None:
    """The startup wall is crossed before command dispatch."""

    _assert_unbridged(_invoke(harness, bun, "run", "--help"))


def test_blank_task_id_refuses_startup(
    harness: Path, bun: Path, tmp_path: Path
) -> None:
    _assert_unbridged(
        _invoke(
            harness,
            bun,
            "--version",
            RANEX_TASK_ID="  ",
            RANEX_EMIT=str(tmp_path / "emit.jsonl"),
        )
    )


def test_relative_emit_path_refuses_startup(harness: Path, bun: Path) -> None:
    _assert_unbridged(
        _invoke(
            harness,
            bun,
            "--version",
            RANEX_TASK_ID="T-1",
            RANEX_EMIT="rel/path.jsonl",
        )
    )


def test_bridged_version_starts(
    harness: Path, bun: Path, tmp_path: Path
) -> None:
    result = _invoke(
        harness,
        bun,
        "--version",
        RANEX_TASK_ID="T-1",
        RANEX_EMIT=str(tmp_path / "emit.jsonl"),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "bridged --version must print a version string"
    assert "unbridged" not in result.stderr.lower()


def test_bridged_version_does_not_emit(
    harness: Path, bun: Path, tmp_path: Path
) -> None:
    emit = tmp_path / "emit.jsonl"
    result = _invoke(
        harness,
        bun,
        "--version",
        RANEX_TASK_ID="T-1",
        RANEX_EMIT=str(emit),
    )

    assert result.returncode == 0, result.stderr
    assert not emit.exists(), "--version must not create an end-of-task emission"


def _invoke_launcher(
    harness: Path, bun: Path, *args: str, **binding: str
) -> subprocess.CompletedProcess[str]:
    """Drive the fork exactly as an operator would: through bin/ranex."""

    return subprocess.run(
        [str(harness / "bin" / "ranex"), *args],
        cwd=harness,
        capture_output=True,
        text=True,
        timeout=120,
        env=_environment(bun, **binding),
        check=False,
    )


def test_launcher_help_names_ranex(
    harness: Path, bun: Path, tmp_path: Path
) -> None:
    """The operator command is `ranex`, and what it prints says so."""

    result = _invoke_launcher(
        harness,
        bun,
        "--help",
        RANEX_TASK_ID="T-1",
        RANEX_EMIT=str(tmp_path / "emit.jsonl"),
    )

    assert result.returncode == 0, result.stderr
    combined = (result.stdout + result.stderr).lower()
    assert "ranex" in combined, "usage must name ranex as the script"
    assert "opencode" not in combined, "help output still says opencode"


def test_launcher_version_names_no_opencode(
    harness: Path, bun: Path, tmp_path: Path
) -> None:
    result = _invoke_launcher(
        harness,
        bun,
        "--version",
        RANEX_TASK_ID="T-1",
        RANEX_EMIT=str(tmp_path / "emit.jsonl"),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "bridged --version must print a version string"
    combined = (result.stdout + result.stderr).lower()
    assert "opencode" not in combined, "version output still says opencode"


def test_launcher_reaches_the_bridge_gate(harness: Path, bun: Path) -> None:
    """bin/ranex is a path to the real gate, not a way around it."""

    _assert_unbridged(_invoke_launcher(harness, bun, "--help"))


def test_mit_attribution_is_retained(harness: Path) -> None:
    """The one place `opencode` must remain: upstream's MIT copyright line."""

    text = (harness / "LICENSE").read_text()
    assert "MIT" in text
    assert "opencode" in text
