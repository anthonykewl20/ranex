"""SLICE-007 §4: the fork's plugin surface is fixed and compiled in.

A lockable plugin surface is the whole game: a gauge the user can recalibrate
through config, npm, or the filesystem is no gauge.  These source contracts
keep every such door shut in the trimmed sibling fork.
"""

from __future__ import annotations

import os
import re
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


def _typescript_sources(harness: Path, *packages: str) -> list[Path]:
    return [
        source
        for package in packages
        for source in (harness / "packages" / package / "src").rglob("*.ts")
    ]


def _external_load_calls(sources: list[Path]) -> list[str]:
    calls = []
    definition = re.compile(r"(?:async )?function loadExternal\s*\(")
    for source in sources:
        for number, line in enumerate(source.read_text().splitlines(), 1):
            if "loadExternal(" in line and not definition.search(line):
                calls.append(f"{source}:{number}")
    return calls


def test_config_plugin_closes_filesystem_discovery_door(harness: Path) -> None:
    """The config filesystem glob door for plugin discovery is closed."""

    source = harness / "packages/ranex/src/config/plugin.ts"
    assert "{plugin,plugins}" not in source.read_text()


def test_plugin_index_closes_config_plugin_origins_door(harness: Path) -> None:
    """The config plugin-origins door into the server plugin loader is closed."""

    source = harness / "packages/ranex/src/plugin/index.ts"
    text = source.read_text()
    assert "plugin_origins" not in text
    assert not _external_load_calls([source])


def test_tui_runtime_closes_external_loading_door(harness: Path) -> None:
    """The TUI runtime's external-plugin loading door is closed."""

    source = harness / "packages/ranex/src/plugin/tui/runtime.ts"
    assert not source.exists() or not _external_load_calls([source])


def test_v2_external_plugin_loader_is_absent(harness: Path) -> None:
    """The V2 external plugin-loader door is closed by removing its module."""

    assert not (harness / "packages/core/src/config/plugin/external.ts").exists()


def test_plugin_install_and_config_patch_door_is_closed(harness: Path) -> None:
    """The install and config-patch door for adding plugins is closed."""

    sources = _typescript_sources(harness, "opencode", "core")
    references = [
        str(source)
        for source in sources
        if "installPlugin(" in source.read_text() or "patchPluginConfig(" in source.read_text()
    ]
    assert not (harness / "packages/ranex/src/plugin/install.ts").exists()
    assert not references, f"plugin install/config patch references remain: {references}"


def test_npm_resolved_plugin_specifiers_are_absent(harness: Path) -> None:
    """The npm-resolved built-in plugin-specifier door is closed."""

    sources = _typescript_sources(harness, "opencode", "core", "tui")
    specifiers = ("opencode-gitlab-auth", "opencode-poe-auth")
    references = [str(source) for source in sources if any(item in source.read_text() for item in specifiers)]
    assert not references, f"npm-resolved plugin specifiers remain: {references}"


def test_no_external_plugin_load_call_sites_remain(harness: Path) -> None:
    """Every remaining external-plugin load call site, the final loading door, is closed."""

    calls = _external_load_calls(_typescript_sources(harness, "opencode", "core", "tui"))
    assert not calls, f"external plugin load calls remain: {calls}"
