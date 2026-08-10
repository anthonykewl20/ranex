"""SLICE-006 criterion 13 — an approved dependency can force the verdict.

This file proves a **limit**, not a defence. Everything Ranex claims about
dependencies holds here and the attack still works:

- the wheel's SHA-256 matches the lock exactly, byte for byte;
- the lock reproduces byte-identically from its manifest under pinned inputs;
- a human approved this exact package set and the delta named the package;
- the store re-verified the bytes on the way out;
- the environment is read-only, offline, and built from nothing else.

And the suite still reports success while a test fails, because pytest loads
every installed `pytest11` entry point before collection and the plugin sets
`session.exitstatus = 0`. ADR-007 sad paths 17 and 18 say **not caught**, and
this file is what makes that sentence executable rather than decorative.

The control matters as much as the demonstration. Without `evilplug` in the
approved set the identical repository records exit 1, so the demonstration
cannot be passing because pytest never ran.

Do not "fix" this test. If a future change makes it fail, that change has
either closed the hole — in which case ADR-007's sad-path table and this
file's name must both be rewritten deliberately — or it has broken the
demonstration and hidden a limit the product promises to state plainly.
"""

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
from ranex.foundation.signing import generate_keypair

EPOCH = "2026-08-04T00:00:00Z"

# The pinned interpreter must be one this uid cannot rewrite, or provisioning
# refuses it — the same rule the rest of the slice is built on.
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
        reason="no system interpreter this uid cannot rewrite",
    ),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def malicious_wheel() -> bytes:
    """A wheel that is honest in every respect except what its code does.

    Correct metadata, correct tags, a real `pytest11` entry point. Nothing
    about the artifact is malformed — which is the point: integrity checks
    have nothing to object to.
    """

    output = io.BytesIO()
    dist_info = "evilplug-1.0.0.dist-info"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "evilplug/__init__.py",
            "def pytest_sessionfinish(session, exitstatus):\n"
            "    # The whole attack. pytest has already reported the failures;\n"
            "    # only the number the world is judged by is replaced.\n"
            "    session.exitstatus = 0\n",
        )
        archive.writestr(
            f"{dist_info}/METADATA",
            "Metadata-Version: 2.1\nName: evilplug\nVersion: 1.0.0\n",
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: ranex-tests\n"
            "Root-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(
            f"{dist_info}/entry_points.txt", "[pytest11]\nevilplug = evilplug\n"
        )
        archive.writestr(f"{dist_info}/RECORD", "")
    return output.getvalue()


@pytest.fixture(scope="module")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> dict[str, bytes]:
    """Real pytest wheels plus the malicious one, keyed by filename.

    pytest must come from the provisioned root, or its plugin loading is not
    the thing under demonstration. The wheels are fetched once; a machine
    without the index skips rather than pretending.
    """

    directory = tmp_path_factory.mktemp("wheelhouse")
    fetched = subprocess.run(
        [
            str(PINNED_PYTHON), "-m", "pip", "download", "pytest",
            "--dest", str(directory), "--only-binary=:all:", "-q",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if fetched.returncode != 0:
        pytest.skip(f"cannot obtain pytest wheels: {fetched.stderr.strip()[:200]}")
    # The lock resolves for every platform the manifest allows, so uv needs
    # candidates for marker-gated dependencies this host will never install.
    # colorama is pytest's win32 dependency; without it in the index the
    # resolution is unsatisfiable and the fixture fails for a reason that has
    # nothing to do with what is being demonstrated. `--no-deps` and a
    # platform override because pip will not fetch it for Linux otherwise.
    extra = subprocess.run(
        [
            str(PINNED_PYTHON), "-m", "pip", "download", "colorama",
            "--dest", str(directory), "--only-binary=:all:", "--no-deps",
            "--platform", "win_amd64", "--python-version", "3.12", "-q",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if extra.returncode != 0:
        pytest.skip(f"cannot obtain colorama: {extra.stderr.strip()[:200]}")
    wheels = {path.name: path.read_bytes() for path in directory.glob("*.whl")}
    if not any(name.startswith("pytest-") for name in wheels):
        pytest.skip("the download produced no pytest wheel")
    wheels["evilplug-1.0.0-py3-none-any.whl"] = malicious_wheel()
    return wheels


@pytest.fixture(scope="module")
def index(wheelhouse: dict[str, bytes]) -> Iterator[str]:
    """A local PEP 691 index serving exactly those wheels, and nothing else."""

    by_project: dict[str, dict[str, bytes]] = {}
    for filename, contents in wheelhouse.items():
        project = filename.split("-")[0].replace("_", "-").lower()
        by_project.setdefault(project, {})[filename] = contents

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
            if self.path.startswith("/simple/") and self.path.endswith("/"):
                project = self.path.removeprefix("/simple/").rstrip("/")
                available = by_project.get(project)
                if available is None:
                    self._send(404, "text/plain", b"no such project")
                    return
                port = self.server.server_port  # type: ignore[attr-defined]
                body = json.dumps(
                    {
                        "meta": {"api-version": "1.0"},
                        "name": project,
                        "files": [
                            {
                                "filename": filename,
                                "url": f"http://127.0.0.1:{port}/wheels/{filename}",
                                "hashes": {"sha256": sha256(contents)},
                                # Before the pinned epoch, or the resolver
                                # filters every candidate away.
                                "upload-time": "2026-08-01T00:00:00Z",
                            }
                            for filename, contents in sorted(available.items())
                        ],
                    }
                ).encode()
                self._send(200, "application/vnd.pypi.simple.v1+json", body)
                return
            if self.path.startswith("/wheels/"):
                contents = wheelhouse.get(self.path.removeprefix("/wheels/"))
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
        yield f"http://127.0.0.1:{server.server_port}/simple/"
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
    # 0555: this uid owns it but cannot write it, so the pin is real without
    # needing root. Identity is bound by the digest either way.
    copy.chmod(0o555)
    return copy


FAILING_TEST = "def test_two_plus_two():\n    assert 2 + 2 == 5\n"

BOUND_COMMAND = ["uv", "run", "--no-project", "pytest", "-q"]

GATES = """\
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: {command}
"""


def build_repository(
    tmp_path: Path, resolver: Path, index: str, *, malicious: bool
) -> tuple[Path, Path, Path]:
    """A committed repository whose only test fails. Returns repo, store, key."""

    root = tmp_path / ("evil" if malicious else "honest")
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)

    dependencies = '["pytest"]' if not malicious else '["pytest", "evilplug"]'
    manifest = (
        '[project]\nname = "demo"\nversion = "0.0.0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = {dependencies}\n\n[tool.uv]\npackage = false\n"
    )
    (root / "pyproject.toml").write_text(manifest)
    (root / "test_truth.py").write_text(FAILING_TEST)

    # The lock is DERIVED, not authored: the demonstration must clear the
    # byte-comparison the same way an honest dependency set does.
    scratch = tmp_path / f"lock-{root.name}"
    scratch.mkdir()
    (scratch / "pyproject.toml").write_text(manifest)
    subprocess.run(
        [
            str(resolver), "lock", "--exclude-newer", EPOCH,
            "--python", str(PINNED_PYTHON), "--index-url", index,
        ],
        cwd=scratch,
        check=True,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path / "lock-home"),
            "UV_NO_CONFIG": "1",
            "UV_CACHE_DIR": str(tmp_path / f"lock-cache-{root.name}"),
            "UV_PYTHON_DOWNLOADS": "never",
        },
    )
    (root / "uv.lock").write_bytes((scratch / "uv.lock").read_bytes())

    governance = root / "governance"
    governance.mkdir()
    (governance / "deps.yaml").write_text(
        "resolver:\n"
        f"  path: {resolver}\n  sha256: {sha256(resolver.read_bytes())}\n"
        f"python:\n  path: {PINNED_PYTHON}\n"
        f"indexes:\n  - {index}\n"
        f'exclude_newer: "{EPOCH}"\n'
    )
    (governance / "gates.yaml").write_text(
        GATES.format(command=json.dumps(BOUND_COMMAND))
    )
    private_key, public_key = generate_keypair()
    (governance / "producers.yaml").write_text(
        f"producers:\n  worker: {public_key}\n"
    )
    key_path = tmp_path / f"{root.name}.key"
    key_path.write_text(private_key + "\n")
    key_path.chmod(0o600)
    (root / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/journal.sqlite3\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", "initial"], check=True
    )
    return root, tmp_path / f"store-{root.name}", key_path


def provision_and_run(
    root: Path, store: Path, key_path: Path, monkeypatch: pytest.MonkeyPatch
) -> int:
    """Walk the operator's whole path: fetch, approve, run. Returns run's exit."""

    monkeypatch.chdir(root)
    monkeypatch.setattr(
        "ranex.cli.main.governed_repository_root", lambda: root.resolve()
    )
    monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
    assert main(["deps", "fetch", "--repository", ".", "--store", str(store)]) == 0
    assert main(["deps", "approve", "--repository", ".", "--approver", "reviewer"]) == 0
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(key_path))
    return main(
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--repository", ".", "--producers", "governance/producers.yaml",
            "--store", str(store), "--", *BOUND_COMMAND,
        ]
    )


def recorded_exit(root: Path) -> int:
    records = json.loads((root / "governance" / "evidence.json").read_text())
    return int(records[0]["exit_code"])


def test_control_the_failing_suite_really_fails(
    tmp_path: Path,
    resolver: Path,
    index: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the malicious wheel, the same repository records failure.

    This is what stops the demonstration below from passing vacuously. A
    "denial that passes because the command never ran" is the decoration the
    slice explicitly warns about; here the identical tree, command and gate
    produce exit 1 from a genuinely failing test.
    """

    root, store, key_path = build_repository(
        tmp_path, resolver, index, malicious=False
    )
    assert provision_and_run(root, store, key_path, monkeypatch) == 1
    assert recorded_exit(root) == 1


def test_an_approved_hash_correct_wheel_forces_success_NOT_CAUGHT(
    tmp_path: Path,
    resolver: Path,
    index: str,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """**NOT CAUGHT.** Every control passes and the verdict is still a lie.

    ADR-007 sad paths 17 and 18, executable. The wheel matched its SHA-256,
    the lock reproduced byte-for-byte, a human approved this exact set, the
    store re-verified on read, and the environment was sealed and offline.
    pytest then auto-loaded the approved plugin before collection and it
    replaced the exit code.

    Ranex records what it observed, faithfully: exit 0. The observation is
    honest; the number it observed is not. Nothing in this slice closes that,
    and no product text may say otherwise — an approved dependency is inside
    the trusted computing base of the command it helps measure.
    """

    root, store, key_path = build_repository(
        tmp_path, resolver, index, malicious=True
    )
    exit_code = provision_and_run(root, store, key_path, monkeypatch)

    assert exit_code == 0, "the demonstration is stale: the plugin no longer lands"
    assert recorded_exit(root) == 0

    # The suite must have RUN and REPORTED the failure. Exit 0 alone would
    # also describe a pytest that never started, and a demonstration that
    # cannot tell those apart proves nothing. pytest's own report goes to the
    # inherited stdout, so the failure is visible on the way past while the
    # number Ranex records says success.
    reported = capfd.readouterr().out
    assert "1 failed" in reported, reported

    # And the gate accepts it. That is the whole cost of the limit: a PASS
    # minted from a suite that failed, with every integrity control green.
    assert (
        main(
            [
                "gate", "evaluate", "HEAD", "--repository", ".",
                "--producers", "governance/producers.yaml",
                "--approver", "reviewer",
            ]
        )
        == 0
    )
