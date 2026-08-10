"""Happy-path integration coverage for in-process dependency commands."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import threading
import zipfile
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

EPOCH = "2026-08-04T00:00:00Z"

# NOT sys.executable: under uv this is a managed interpreter beneath
# ~/.local/share, which the observed uid can rewrite — and provisioning
# refuses a writable interpreter for exactly that reason. The pin has to be
# a real system interpreter, so a machine without one skips rather than
# neutralising the rule the test depends on.
PINNED_PYTHON = next(
    (
        candidate
        for candidate in (
            Path("/usr/bin/python3.12"),
            Path("/usr/bin/python3.11"),
            Path("/usr/bin/python3"),
        )
        if candidate.is_file() and not os.access(candidate, os.W_OK)
    ),
    None,
)


pytestmark = [
    pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed"),
    pytest.mark.skipif(
        PINNED_PYTHON is None,
        reason="no system interpreter this uid cannot rewrite; the pin would be meaningless",
    ),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wheel(name: str, version: str) -> bytes:
    """Build the smallest valid pure-Python wheel needed by uv and ranex."""

    output = io.BytesIO()
    dist_info = f"{name}-{version}.dist-info"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{name}/__init__.py", f"VERSION = {version!r}\n")
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: ranex-tests\n"
            "Root-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(f"{dist_info}/RECORD", "")
    return output.getvalue()


@pytest.fixture(scope="module")
def package_index() -> Iterator[tuple[str, dict[str, bytes]]]:
    wheels = {
        "tinypkg-1.0.0-py3-none-any.whl": wheel("tinypkg", "1.0.0"),
        "tinypkg-2.0.0-py3-none-any.whl": wheel("tinypkg", "2.0.0"),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: object) -> None:
            pass

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(body)

        def _respond(self) -> None:
            if self.path == "/simple/tinypkg/":
                files = []
                for filename, contents in wheels.items():
                    files.append(
                        {
                            "filename": filename,
                            "url": f"http://127.0.0.1:{self.server.server_port}/wheels/{filename}",  # type: ignore[attr-defined]
                            "hashes": {"sha256": sha256(contents)},
                            "upload-time": "2026-08-01T00:00:00Z",
                        }
                    )
                body = json.dumps(
                    {"meta": {"api-version": "1.0"}, "name": "tinypkg", "files": files}
                ).encode()
                self._send(200, "application/vnd.pypi.simple.v1+json", body)
                return
            if self.path.startswith("/wheels/"):
                contents = wheels.get(self.path.removeprefix("/wheels/"))
                if contents is not None:
                    self._send(200, "application/octet-stream", contents)
                    return
            self._send(404, "text/plain", b"not found")

        def do_GET(self) -> None:
            self._respond()

        def do_HEAD(self) -> None:
            self._respond()

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/simple/", wheels
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.fixture()
def resolver(tmp_path: Path) -> Path:
    source = shutil.which("uv")
    assert source is not None
    copy = tmp_path / "uv"
    shutil.copy(source, copy)
    copy.chmod(0o555)
    return copy


def project(dependency: str | None) -> str:
    dependencies = "[]" if dependency is None else f'["tinypkg=={dependency}"]'
    return (
        "[project]\nname = \"demo\"\nversion = \"0.0.0\"\n"
        'requires-python = ">=3.11"\n'
        f"dependencies = {dependencies}\n\n[tool.uv]\npackage = false\n"
    )


def lock_for(tmp_path: Path, resolver: Path, index: str, manifest: str) -> bytes:
    scratch = tmp_path / f"lock-scratch-{sha256(manifest.encode())[:12]}"
    scratch.mkdir()
    (scratch / "pyproject.toml").write_text(manifest)
    cache = tmp_path / f"lock-cache-{sha256(manifest.encode())[:12]}"
    environment = {"UV_NO_CONFIG": "1", "UV_CACHE_DIR": str(cache), "HOME": str(tmp_path / "lock-home"), "UV_PYTHON_DOWNLOADS": "never"}
    subprocess.run(
        [str(resolver), "lock", "--exclude-newer", EPOCH, "--python", str(PINNED_PYTHON),
         "--index-url", index],
        cwd=scratch, env=environment, check=True, capture_output=True, text=True,
    )
    return (scratch / "uv.lock").read_bytes()


def commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


@pytest.fixture()
def repo(tmp_path: Path, resolver: Path, package_index: tuple[str, dict[str, bytes]]) -> Iterator[tuple[Path, Path, dict[str, bytes]]]:
    index, wheels = package_index
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    manifest = project("1.0.0")
    (root / "pyproject.toml").write_text(manifest)
    (root / "uv.lock").write_bytes(lock_for(tmp_path, resolver, index, manifest))
    governance = root / "governance"
    governance.mkdir()
    (governance / "deps.yaml").write_text(
        "resolver:\n"
        f"  path: {resolver}\n  sha256: {sha256(resolver.read_bytes())}\n"
        "python:\n"
        f"  path: {PINNED_PYTHON}\n"
        f"indexes:\n  - {index}\nexclude_newer: \"{EPOCH}\"\n"
    )
    (governance / "producers.yaml").write_text("producers: {}\n")
    (governance / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n    required_claims: []\n"
    )
    (root / ".gitignore").write_text("governance/evidence.json\ngovernance/journal.sqlite3\n")
    commit(root, "initial")
    yield root, tmp_path / "store", wheels


def invoke(root: Path, argv: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.chdir(root)
    monkeypatch.setattr("ranex.cli.main.governed_repository_root", lambda: root.resolve())
    return main(argv)


def fetch(root: Path, store: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    return invoke(root, ["deps", "fetch", "--repository", ".", "--store", str(store)], monkeypatch)


def approve(root: Path, monkeypatch: pytest.MonkeyPatch, approver: str = "reviewer") -> int:
    return invoke(root, ["deps", "approve", "--repository", ".", "--approver", approver], monkeypatch)


def relock_and_commit(root: Path, tmp_path: Path, resolver: Path, index: str, dependency: str | None, message: str) -> None:
    manifest = project(dependency)
    (root / "pyproject.toml").write_text(manifest)
    (root / "uv.lock").write_bytes(lock_for(tmp_path, resolver, index, manifest))
    commit(root, message)


def test_fetch_provisions_and_records_a_derivation(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, store, wheels = repo
    assert fetch(root, store, monkeypatch) == 0
    output = capsys.readouterr().out
    assert "FETCHED" in output and "depset=" in output and "not yet approved" in output
    records = [entry for entry in Journal(root / "governance/journal.sqlite3").entries() if entry["type"] == "deps-derivation"]
    assert len(records) == 1
    assert records[0]["lock_sha256"] == sha256((root / "uv.lock").read_bytes())
    assert records[0]["packages"] == {"tinypkg": "1.0.0"}
    digest = sha256(wheels["tinypkg-1.0.0-py3-none-any.whl"])
    entry = store / "sha256" / digest
    assert entry.read_bytes() == wheels["tinypkg-1.0.0-py3-none-any.whl"]
    assert sha256(entry.read_bytes()) == digest


def test_second_fetch_reuses_the_store_and_downloads_nothing(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, store, _ = repo
    assert fetch(root, store, monkeypatch) == 0
    capsys.readouterr()
    before = {path: path.stat().st_ino for path in (store / "sha256").iterdir()}
    assert fetch(root, store, monkeypatch) == 0
    output = capsys.readouterr().out
    assert "reused=1" in output and "downloaded=0" in output
    assert {path: path.stat().st_ino for path in (store / "sha256").iterdir()} == before


def test_approve_records_the_full_set_when_there_is_no_baseline(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, store, _ = repo
    assert fetch(root, store, monkeypatch) == 0
    capsys.readouterr()
    assert approve(root, monkeypatch) == 0
    output = capsys.readouterr().out
    assert "no prior approval" in output and "+ tinypkg 1.0.0" in output and "APPROVED" in output
    assert "approval reduces hidden change" in output
    approvals = [entry for entry in Journal(root / "governance/journal.sqlite3").entries() if entry["type"] == "deps-approval"]
    assert len(approvals) == 1 and approvals[0]["approver_id"] == "reviewer"


def test_approve_renders_added_removed_and_changed(repo: tuple[Path, Path, dict[str, bytes]], resolver: Path, package_index: tuple[str, dict[str, bytes]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, store, _ = repo
    index, _ = package_index
    assert fetch(root, store, monkeypatch) == 0
    assert approve(root, monkeypatch) == 0
    capsys.readouterr()
    relock_and_commit(root, tmp_path, resolver, index, "2.0.0", "upgrade")
    assert fetch(root, store, monkeypatch) == 0
    capsys.readouterr()
    assert approve(root, monkeypatch) == 0
    assert "~ tinypkg 1.0.0 -> 2.0.0" in capsys.readouterr().out
    relock_and_commit(root, tmp_path, resolver, index, None, "remove")
    assert fetch(root, store, monkeypatch) == 0
    capsys.readouterr()
    assert approve(root, monkeypatch) == 0
    assert "- tinypkg 2.0.0" in capsys.readouterr().out


def test_fetch_refuses_a_store_inside_the_repository(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, _, _ = repo
    assert fetch(root, root / "store", monkeypatch) == 2
    assert "refusing a wheel store inside the governed repository" in capsys.readouterr().err


def test_fetch_refuses_a_manifest_without_a_project_name(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, store, _ = repo
    (root / "pyproject.toml").write_text("[tool.uv]\npackage = false\n")
    commit(root, "remove project name")
    assert fetch(root, store, monkeypatch) == 2
    assert "declares no project name" in capsys.readouterr().err


def test_approve_refuses_a_blank_approver(repo: tuple[Path, Path, dict[str, bytes]], monkeypatch: pytest.MonkeyPatch) -> None:
    root, _, _ = repo
    assert approve(root, monkeypatch, "   ") == 2


def test_fetch_refuses_a_name_that_is_not_a_string(
    repo: tuple[Path, Path, dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Input: [project].name present but not a string. TOML allows it, and the
    # lock's root package is looked up by that name, so a non-string manifest
    # cannot say which package is the root.
    root, store, _ = repo
    (root / "pyproject.toml").write_text(
        '[project]\nname = 5\nversion = "0.0.0"\nrequires-python = ">=3.11"\n'
        "dependencies = []\n\n[tool.uv]\npackage = false\n"
    )
    commit(root, "a manifest whose name is a number")
    assert fetch(root, store, monkeypatch) == 2
    assert "declares no project name" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["fetch", "approve"])
def test_second_repository_targets_are_refused(
    repo: tuple[Path, Path, dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    # Input: --repository naming a tree that is not the governed one. Both
    # deps commands refuse it exactly as run and gate evaluate do — a second
    # repository is a second subject, and neither command judges two.
    root, store, _ = repo
    # A path INSIDE the repository, so containment accepts it and the
    # second-repository check is the thing that refuses. An absolute path
    # outside is rejected a step earlier and would prove a different rule.
    inside = root / "subproject"
    inside.mkdir()
    (inside / "keep.txt").write_text("x\n")
    commit(root, "add a subdirectory")
    argv = (
        ["deps", "fetch", "--repository", "subproject", "--store", str(store)]
        if command == "fetch"
        else ["deps", "approve", "--repository", "subproject", "--approver", "r"]
    )
    assert invoke(root, argv, monkeypatch) == 2
    assert "second-repository targets are refused" in capsys.readouterr().err


def test_approve_refuses_a_subject_without_pins(
    repo: tuple[Path, Path, dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Input: the committed pins are removed, so nothing declares dependencies.
    # Absence blocks — there is no set to approve, and silence is not an empty
    # approval.
    root, _store, _ = repo
    subprocess.run(
        ["git", "-C", str(root), "rm", "-q", "governance/deps.yaml"], check=True
    )
    commit(root, "drop the pins")
    assert approve(root, monkeypatch) == 2
    assert "nothing to approve" in capsys.readouterr().err
