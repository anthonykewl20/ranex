"""Real CLI freeze/check journeys; no candidate code or mocked Git runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import canonical_payload_bytes

REPO = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", "specification", *args],
        cwd=REPO, env={**os.environ, "PYTHONPATH": str(REPO / "src")},
        capture_output=True, text=True,
    )


def setup_subject(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "product"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "probe@example.invalid")
    git(root, "config", "user.name", "Probe")
    (root / "acceptance").mkdir()
    (root / "acceptance/probe.py").write_text("import urllib.request\n")
    (root / "acceptance/fixture.json").write_text('{"tenant":"alice"}\n')
    (root / "product.py").write_text("print('product')\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "baseline")
    vectors = json.loads((REPO / "tests/contract/fixtures/specification/abc-v1-vectors.json").read_text())
    packet = tmp_path / "A.json"
    packet.write_bytes(canonical_payload_bytes(vectors["triple"]["a"]))
    invocation = tmp_path / "argv.json"
    invocation.write_bytes(canonical_payload_bytes(["python", "acceptance/probe.py"]))
    return root, packet, invocation


def freeze(root: Path, packet: Path, invocation: Path, output: Path):
    return cli("freeze-probes", "--external-repository", str(root), "--spec-packet", str(packet),
               "--invocation", str(invocation), "--root", "acceptance", "--output", str(output))


def test_freeze_is_repeatable_and_candidate_product_changes_are_allowed(tmp_path: Path) -> None:
    root, packet, invocation = setup_subject(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    a = freeze(root, packet, invocation, first)
    assert a.returncode == 0, a.stderr
    b = freeze(root, packet, invocation, second)
    assert b.returncode == 0, b.stderr
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    record = json.loads(a.stdout)
    assert record["status"] == "FROZEN"
    (root / "product.py").write_text("print('repaired product')\n")
    git(root, "commit", "-qam", "repair")
    checked = cli("check-probes", "--external-repository", str(root), "--bundle", str(first),
                  "--manifest-digest", record["manifest_digest"])
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["status"] == "PROBES-UNCHANGED"
    assert "PASS" not in checked.stdout


@pytest.mark.parametrize("attack", ["edit", "add", "delete", "mode", "symlink", "bundle", "pin", "bundle-mode", "argv", "fifo"])
def test_probe_tampering_cannot_satisfy_the_frozen_identity(tmp_path: Path, attack: str) -> None:
    root, packet, invocation = setup_subject(tmp_path)
    bundle = tmp_path / "bundle"
    frozen = freeze(root, packet, invocation, bundle)
    assert frozen.returncode == 0, frozen.stderr
    digest = json.loads(frozen.stdout)["manifest_digest"]
    target = root / "acceptance/probe.py"
    if attack == "edit":
        target.write_text("assert True\n")
    elif attack == "add":
        (root / "acceptance/conftest.py").write_text("# replace fixtures\n")
    elif attack == "delete":
        target.unlink()
    elif attack == "mode":
        target.chmod(0o755)
    elif attack == "symlink":
        target.unlink()
        target.symlink_to("../product.py")
    elif attack == "bundle":
        (bundle / "probes/acceptance/probe.py").write_text("assert True\n")
    elif attack == "bundle-mode":
        (bundle / "probes/acceptance/probe.py").chmod(0o700)
    elif attack == "argv":
        descriptor = json.loads((bundle / "probe-contract.json").read_bytes())
        descriptor["argv"] = ["true"]
        (bundle / "probe-contract.json").write_bytes(canonical_payload_bytes(descriptor))
    elif attack == "fifo":
        target = bundle / "probes/acceptance/probe.py"
        target.unlink()
        os.mkfifo(target)
    else:
        digest = "sha256:" + "0" * 64
    if attack not in {"bundle", "pin", "bundle-mode", "argv", "fifo"}:
        git(root, "add", "-A")
        git(root, "commit", "-qm", attack)
    checked = cli("check-probes", "--external-repository", str(root), "--bundle", str(bundle),
                  "--manifest-digest", digest)
    assert checked.returncode == 2, checked.stdout
    assert "PROBES-UNCHANGED" not in checked.stdout


def test_freeze_refuses_dirty_tree_internal_output_and_placeholder(tmp_path: Path) -> None:
    root, packet, invocation = setup_subject(tmp_path)
    internal = freeze(root, packet, invocation, root / "bundle")
    assert internal.returncode == 2
    assert not (root / "bundle").exists()
    (root / "acceptance/probe.py").write_text("# ranex-gauge: placeholder-until-execution-slice\n")
    dirty = freeze(root, packet, invocation, tmp_path / "dirty")
    assert dirty.returncode == 2
    git(root, "commit", "-qam", "placeholder")
    placeholder = freeze(root, packet, invocation, tmp_path / "placeholder")
    assert placeholder.returncode == 2
    assert "PLACEHOLDER" in placeholder.stderr
    assert not (tmp_path / "placeholder").exists()
