"""SLICE-007 §1: the trimmed fork keeps exactly the keep-set and builds at the pin.

The fork lives outside this repository (a sibling clone, rebaseable against
upstream). These tests read that tree and its git history directly — never a
report about them. On a machine without the fork they skip loudly, the same
convention CI already prints for the bind-mount identity tests: a governance
test that vanishes silently is the same "nothing ran" hole this suite exists
to close.

Red-then-green: written against the untrimmed pin, every cut assertion below
fails until the trim lands, and the build assertion holds only when the
manifest edits for the cuts land with it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

# ADR-008: the 40-hex commit is the pin, not the tag.
PIN = "012c2f57f976489d88bd4598a056b4bdcdd428ee"

# ADR-008 Decision Outcome. `effect-sqlite-node` is cut as unimported — the
# slice's design list carries a drafting slip; the ADR governs.
KEEP_PACKAGES = (
    "cli",
    "core",
    "effect-drizzle-sqlite",
    "llm",
    # renamed from "opencode" by the 2026-08-07 rebrand; the app package
    # keeps its role, only its directory name changed.
    "ranex",
    "plugin",
    "protocol",
    "schema",
    "sdk",
    "server",
    "tui",
)
CUT_PACKAGES = (
    "app",
    "client",
    "codemode",
    "console",
    "containers",
    "desktop",
    "docs",
    "effect-sqlite-node",
    "enterprise",
    "function",
    "http-recorder",
    "httpapi-codegen",
    "identity",
    "script",
    "sdk-next",
    "session-ui",
    "slack",
    "stats",
    "storybook",
    "ui",
    "web",
)
CUT_TOP_LEVEL = (
    "artifacts",
    "github",
    "infra",
    "nix",
    "perf",
    "script",
    "sdks",
    "sst.config.ts",
)


def _harness_dir() -> Path:
    default = Path(__file__).resolve().parents[2].parent / "ranex-harness"
    return Path(os.environ.get("RANEX_HARNESS_DIR", default))


@pytest.fixture(scope="module")
def harness() -> Path:
    tree = _harness_dir()
    if not (tree / "package.json").is_file():
        pytest.skip(f"harness fork not present at {tree} (set RANEX_HARNESS_DIR)")
    return tree


def test_fork_history_contains_the_pin(harness: Path) -> None:
    """The trim is commits on top of the pinned commit, never a re-clone."""

    proof = subprocess.run(
        ["git", "-C", str(harness), "merge-base", "--is-ancestor", PIN, "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proof.returncode == 0, f"pin {PIN} is not an ancestor of HEAD"


def test_cut_packages_are_absent(harness: Path) -> None:
    present = [name for name in CUT_PACKAGES if (harness / "packages" / name).exists()]
    assert not present, f"cut packages still in tree: {present}"


def test_cut_top_level_items_are_absent(harness: Path) -> None:
    present = [name for name in CUT_TOP_LEVEL if (harness / name).exists()]
    assert not present, f"cut top-level items still in tree: {present}"


def test_keep_set_is_present(harness: Path) -> None:
    missing = [
        name for name in KEEP_PACKAGES if not (harness / "packages" / name).is_dir()
    ]
    assert not missing, f"keep-set packages missing: {missing}"
    assert (harness / "patches").is_dir(), "top-level patches/ is load-bearing"


def test_root_manifest_drops_husky_and_cut_scripts(harness: Path) -> None:
    """ADR-008 prior art: the fork inherits husky from `prepare` and removes it.

    Root scripts that shell into cut trees (`script/…`) are the manifest edits
    the slice names — asserted here so a lazy trim that deletes directories but
    leaves the wiring cannot read as done.
    """

    root = json.loads((harness / "package.json").read_text())
    scripts = root.get("scripts", {})
    assert "husky" not in scripts.get("prepare", ""), "husky survives in prepare"
    stale = {
        name: line
        for name, line in scripts.items()
        if "script/" in line or "sst " in line or "--cwd packages/console" in line
    }
    assert not stale, f"root scripts still reach cut trees: {stale}"


def test_no_kept_manifest_depends_on_a_cut_package(harness: Path) -> None:
    """Deleting a directory is not a trim if the workspace still asks for it."""

    cut_names = set()
    for manifest in (harness / "packages").glob("*/package.json"):
        if manifest.parent.name in CUT_PACKAGES:
            cut_names.add(json.loads(manifest.read_text()).get("name"))
    # After the cut the directories are gone, so derive the workspace names the
    # scheme uses for them instead of trusting what remains.
    cut_names |= {f"@ranex/{name}" for name in CUT_PACKAGES}
    offenders = {}
    for name in KEEP_PACKAGES:
        manifest = harness / "packages" / name / "package.json"
        data = json.loads(manifest.read_text())
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            hits = sorted(set(data.get(section, {})) & cut_names)
            if hits:
                offenders[f"{name}:{section}"] = hits
    assert not offenders, f"kept manifests still depend on cut packages: {offenders}"


def test_keep_set_builds_at_the_pin(harness: Path) -> None:
    """The whole trimmed workspace typechecks — the gears still turn.

    Turbo caches an unchanged tree, so a green re-run costs about a second;
    a real change pays the full check once. Absence of the toolchain skips
    loudly rather than passing vacuously.
    """

    bun = shutil.which("bun") or str(Path.home() / ".bun" / "bin" / "bun")
    if not Path(bun).is_file():
        pytest.skip("bun toolchain not installed on this machine")
    if not (harness / "node_modules").is_dir():
        pytest.skip("harness dependencies not installed (run `bun install`)")
    # turbo re-invokes `bun` by name, so the toolchain's directory must be on
    # PATH for the child even when the test found it by absolute path.
    env = dict(os.environ)
    env["PATH"] = f"{Path(bun).parent}{os.pathsep}{env.get('PATH', '')}"
    build = subprocess.run(
        [bun, "turbo", "typecheck"],
        cwd=harness,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
        check=False,
    )
    assert build.returncode == 0, (
        f"trimmed workspace does not typecheck:\n{build.stdout[-4000:]}"
        f"\n{build.stderr[-4000:]}"
    )
