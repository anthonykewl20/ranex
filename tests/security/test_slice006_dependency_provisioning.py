"""SLICE-006 — provisioning refusals at the CLI boundary.

The unit file froze the pure core. This file freezes the two commands and the
run integration around it: `deps fetch` (the only networked phase), `deps
approve`, and the provisioned `run` path. Every test here is a refusal or a
denial; the honest pipeline lives in `tests/e2e/test_gating_real_suite.py`.

Frozen contract:

- `ranex deps fetch --repository . --store <dir>` derives a clean lock with
  the pinned resolver, byte-compares it against the committed one, admits
  wheels into the store, and appends a `deps-derivation` record to the
  journal. Refusals exit 2 and leave both store and journal without the
  corresponding entry.
- `ranex deps approve --approver <id>` appends a `deps-approval` record for
  the current depset. It refuses a lock the journal never saw derived.
- `ranex run` on a subject whose commit carries `governance/deps.yaml`
  requires: a `deps-derivation` record for the committed lock's sha256, a
  `deps-approval` record for the current depset digest, and a verified store
  entry per selected wheel — all before spawning. The command then runs with
  `UV_PROJECT_ENVIRONMENT`, `UV_NO_SYNC=1`, `UV_OFFLINE=1`, a read-only
  dependency root, and no network.

Fixture resolvers live in user-writable locations, so tests that are not
about the writability rule neutralise it via monkeypatch; the two tests that
are about it run unpatched.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.deps import DepsApproval, DepsDerivation
from ranex.provisioning.approval import depset_digest
from ranex.provisioning.store import WheelStore
from ranex.provisioning.target import probe_target

REAL_UV = shutil.which("uv")

pytestmark = pytest.mark.skipif(REAL_UV is None, reason="uv is not installed")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_wheel(name: str, version: str, body: str) -> bytes:
    """A minimal, honest pure-python wheel built in memory."""

    import io

    buffer = io.BytesIO()
    prefix = f"{name}-{version}"
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{name}/__init__.py", body)
        archive.writestr(
            f"{prefix}.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        )
        archive.writestr(
            f"{prefix}.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: ranex-tests\n"
            "Root-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(f"{prefix}.dist-info/RECORD", "")
    return buffer.getvalue()


FAKEPKG_WHEEL = build_wheel("fakepkg", "1.0.0", "VALUE = 42\n")


PINS_TEMPLATE = """\
resolver:
  path: {resolver}
  sha256: {resolver_digest}
python:
  path: {python}
indexes:
  - https://pypi.org/simple
exclude_newer: "2026-08-04T00:00:00Z"
"""


def locked_project(dependency: bool) -> tuple[str, str]:
    """A pyproject and a hand-authored lock of the shape uv writes.

    The dependency-bearing variant is used only on the run path, which never
    re-derives; the fetch tests use the zero-dependency variant, whose clean
    derivation needs no index at all.
    """

    requires = '["fakepkg==1.0.0"]' if dependency else "[]"
    pyproject = (
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = {requires}\n"
        "\n[tool.uv]\npackage = false\n"
    )
    fake = (
        f"""
[[package]]
name = "fakepkg"
version = "1.0.0"
source = {{ registry = "https://pypi.org/simple" }}
wheels = [
    {{ url = "https://files.example/fakepkg-1.0.0-py3-none-any.whl", hash = "sha256:{sha256(FAKEPKG_WHEEL)}" }},
]
"""
        if dependency
        else ""
    )
    dependencies = (
        'dependencies = [\n    { name = "fakepkg" },\n]\n' if dependency else ""
    )
    lock = (
        "version = 1\n"
        "revision = 3\n"
        'requires-python = ">=3.11"\n'
        "\n[options]\n"
        'exclude-newer = "2026-08-04T00:00:00Z"\n'
        f"{fake}"
        "\n[[package]]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "source = { virtual = \".\" }\n"
        f"{dependencies}"
    )
    return pyproject, lock


GATES = """\
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: {command}
"""


@pytest.fixture()
def allow_fixture_binaries(monkeypatch: pytest.MonkeyPatch):
    """Neutralise the writability rule for tests that are not about it."""

    monkeypatch.setattr(
        "ranex.provisioning.pins.refuse_writable_executable", lambda _path: None
    )


class DepsRepo:
    """A committed repository carrying pins, manifest, lock and gate."""

    def __init__(self, root: Path, key_path: Path, journal: Path, store: Path):
        self.root = root
        self.key_path = key_path
        self.journal = journal
        self.store = store

    def entries(self) -> list[dict[str, object]]:
        if not self.journal.exists():
            return []
        return Journal(self.journal).entries()

    def evidence(self) -> object | None:
        path = self.root / "governance" / "evidence.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())


def make_repo(
    tmp_path: Path,
    *,
    dependency: bool,
    command: list[str],
    pins_text: str | None = None,
    lock_override: str | None = None,
    resolver: str | None = None,
    commit_pins: bool = True,
) -> DepsRepo:
    repo = tmp_path / "governed"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(repo), "config", key, value], check=True)

    pyproject, lock = locked_project(dependency)
    (repo / "pyproject.toml").write_text(pyproject)
    (repo / "uv.lock").write_text(lock_override if lock_override is not None else lock)

    governance = repo / "governance"
    governance.mkdir()
    resolver_path = resolver if resolver is not None else REAL_UV
    if pins_text is None:
        pins_text = PINS_TEMPLATE.format(
            resolver=resolver_path,
            resolver_digest=sha256(Path(resolver_path).read_bytes()),
            python=sys.executable,
        )
    (governance / "deps.yaml").write_text(pins_text)
    (governance / "gates.yaml").write_text(GATES.format(command=json.dumps(command)))

    private_key, public_key = generate_keypair()
    (governance / "producers.yaml").write_text(f"producers:\n  worker: {public_key}\n")
    key_path = tmp_path / "keys" / "worker.key"
    key_path.parent.mkdir(exist_ok=True)
    key_path.write_text(private_key + "\n")
    key_path.chmod(0o600)

    (repo / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/journal.sqlite3\n"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    if not commit_pins:
        subprocess.run(
            ["git", "-C", str(repo), "rm", "-q", "--cached", "governance/deps.yaml"],
            check=True,
        )
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "initial"], check=True)
    return DepsRepo(
        repo,
        key_path,
        repo / "governance" / "journal.sqlite3",
        tmp_path / "store",
    )


def invoke(
    repo: DepsRepo, argv: list[str], monkeypatch: pytest.MonkeyPatch, *, sign: bool = False
) -> int:
    monkeypatch.chdir(repo.root)
    monkeypatch.setattr(
        "ranex.cli.main.governed_repository_root", lambda: repo.root.resolve()
    )
    if sign:
        monkeypatch.setenv("RANEX_SIGNING_KEY", str(repo.key_path))
    else:
        monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
    return main(argv)


def fetch(repo: DepsRepo, monkeypatch: pytest.MonkeyPatch) -> int:
    return invoke(
        repo,
        ["deps", "fetch", "--repository", ".", "--store", str(repo.store)],
        monkeypatch,
    )


def approve(repo: DepsRepo, monkeypatch: pytest.MonkeyPatch) -> int:
    return invoke(
        repo,
        ["deps", "approve", "--repository", ".", "--approver", "reviewer"],
        monkeypatch,
    )


def run(repo: DepsRepo, command: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim",
            "tests-executed",
            "--producer",
            "worker",
            "--repository",
            ".",
            "--producers",
            "governance/producers.yaml",
            "--store",
            str(repo.store),
            "--",
            *command,
        ],
        monkeypatch,
        sign=True,
    )


def committed_lock_bytes(repo: DepsRepo) -> bytes:
    return (repo.root / "uv.lock").read_bytes()


def record_derivation(repo: DepsRepo) -> None:
    """The record `deps fetch` would have appended, for run-path tests."""

    lock = committed_lock_bytes(repo)
    target = probe_target(Path(sys.executable))
    Journal(repo.journal).append(
        DepsDerivation(
            lock_sha256=sha256(lock),
            depset_digest=depset_digest(lock, target),
            packages={"fakepkg": "1.0.0"},
        )
    )


def record_approval(repo: DepsRepo, digest: str | None = None) -> None:
    lock = committed_lock_bytes(repo)
    target = probe_target(Path(sys.executable))
    Journal(repo.journal).append(
        DepsApproval(
            depset_digest=digest or depset_digest(lock, target),
            packages={"fakepkg": "1.0.0"},
            approver_id="reviewer",
        )
    )


def load_store(repo: DepsRepo) -> None:
    WheelStore(repo.store).publish(sha256(FAKEPKG_WHEEL), FAKEPKG_WHEEL)


RUN_COMMAND = [
    "uv",
    "run",
    "--no-project",
    "python",
    "-c",
    "import fakepkg; raise SystemExit(0 if fakepkg.VALUE == 42 else 5)",
]


# --------------------------------------------------------------------------
# `deps fetch` refusals. (ADR-007 sad paths 1, 2, 3, 4; criteria 1, 2, 3)
# --------------------------------------------------------------------------


class TestFetchRefusals:
    def test_absent_manifest_refuses_before_anything(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 1: no supported manifest — never guess dependencies.
        repo = make_repo(tmp_path, dependency=False, command=["sh", "-c", "true"])
        subprocess.run(["git", "-C", str(repo.root), "rm", "-q", "pyproject.toml"], check=True)
        subprocess.run(
            ["git", "-C", str(repo.root), "commit", "-q", "-m", "drop manifest"],
            check=True,
        )
        (repo.root / "pyproject.toml").unlink(missing_ok=True)
        assert fetch(repo, monkeypatch) == 2
        assert "pyproject.toml" in capsys.readouterr().err
        assert not repo.store.exists() or not any(repo.store.rglob("*"))
        assert repo.entries() == []

    def test_absent_committed_lock_refuses(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 2: absence cannot mean empty.
        repo = make_repo(tmp_path, dependency=False, command=["sh", "-c", "true"])
        subprocess.run(["git", "-C", str(repo.root), "rm", "-q", "uv.lock"], check=True)
        subprocess.run(
            ["git", "-C", str(repo.root), "commit", "-q", "-m", "drop lock"], check=True
        )
        (repo.root / "uv.lock").unlink(missing_ok=True)
        assert fetch(repo, monkeypatch) == 2
        assert "uv.lock" in capsys.readouterr().err
        assert repo.entries() == []

    def test_uncommitted_pins_refuse(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # The pins are a trust root: a file no commit carries decides nothing.
        repo = make_repo(
            tmp_path, dependency=False, command=["sh", "-c", "true"], commit_pins=False
        )
        assert fetch(repo, monkeypatch) == 2
        assert "deps.yaml" in capsys.readouterr().err

    def test_hand_edited_lock_fails_byte_comparison(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 3 / criterion 2: the committed lock claims a package the clean
        # derivation does not produce. The comparison is byte equality of the
        # regenerated file, not uv's own --check.
        _, honest_lock = locked_project(False)
        repo = make_repo(
            tmp_path,
            dependency=False,
            command=["sh", "-c", "true"],
            lock_override=honest_lock.replace(
                'requires-python = ">=3.11"',
                'requires-python = ">=3.11"\n\n# hand edit\n',
                1,
            ),
        )
        assert fetch(repo, monkeypatch) == 2
        error = capsys.readouterr().err
        assert "differs" in error or "match" in error
        assert repo.entries() == []

    def test_replaced_resolver_bytes_refuse(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # Criterion 3: the pinned digest is of the resolver that was approved;
        # a binary with other bytes at that path is not that resolver.
        assert REAL_UV is not None
        wrong = sha256(Path(REAL_UV).read_bytes() + b"tampered")
        pins = PINS_TEMPLATE.format(
            resolver=REAL_UV, resolver_digest=wrong, python=sys.executable
        )
        repo = make_repo(
            tmp_path, dependency=False, command=["sh", "-c", "true"], pins_text=pins
        )
        assert fetch(repo, monkeypatch) == 2
        assert "sha256" in capsys.readouterr().err
        assert repo.entries() == []

    def test_user_writable_resolver_refuses_unpatched(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Criterion 3, the writability half, deliberately NOT neutralised: a
        # resolver the observed uid can rewrite is agent-selected whatever its
        # bytes were when the pin was written.
        assert REAL_UV is not None
        writable = tmp_path / "uv"
        writable.write_bytes(Path(REAL_UV).read_bytes())
        writable.chmod(0o755)
        pins = PINS_TEMPLATE.format(
            resolver=writable,
            resolver_digest=sha256(writable.read_bytes()),
            python=sys.executable,
        )
        repo = make_repo(
            tmp_path,
            dependency=False,
            command=["sh", "-c", "true"],
            pins_text=pins,
        )
        assert fetch(repo, monkeypatch) == 2
        assert "writable" in capsys.readouterr().err


# --------------------------------------------------------------------------
# `deps approve` refusals.
# --------------------------------------------------------------------------


class TestApproveRefusals:
    def test_approving_an_underived_lock_refuses(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # Approval spends human attention on a delta; a lock nothing derived
        # is a delta of unverified bytes and must not be approvable.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        assert approve(repo, monkeypatch) == 2
        assert "deriv" in capsys.readouterr().err.lower()
        assert all(
            entry.get("type") != "deps-approval" for entry in repo.entries()
        )


# --------------------------------------------------------------------------
# The provisioned `run` path. (sad paths 9, 12–16; criteria 6, 7, 8, 9)
# --------------------------------------------------------------------------


class TestRunRefusals:
    def test_underived_lock_refuses_before_spawn(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # Criterion 2 at the run boundary: a committed lock the journal never
        # saw derived may be entirely agent-authored.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        load_store(repo)
        record_approval(repo)
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "deriv" in capsys.readouterr().err.lower()
        assert repo.evidence() is None

    def test_unapproved_depset_refuses_before_spawn(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 15/16 / criterion 9: no approval, no execution.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        load_store(repo)
        record_derivation(repo)
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "approv" in capsys.readouterr().err.lower()
        assert repo.evidence() is None

    def test_approval_of_a_different_depset_refuses(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo, digest="sha256:" + "0" * 64)
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "approv" in capsys.readouterr().err.lower()
        assert repo.evidence() is None

    def test_missing_store_entry_refuses_before_spawn(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 12 / criterion 6: an empty store is a refusal, never a fetch.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        record_derivation(repo)
        record_approval(repo)
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "fakepkg" in capsys.readouterr().err
        assert repo.evidence() is None

    def test_corrupt_store_entry_quarantines_and_refuses(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # s.p. 9: the run never repairs, downloads, or serves corruption.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)
        entry = repo.store / "sha256" / sha256(FAKEPKG_WHEEL)
        entry.chmod(0o600)
        entry.write_bytes(b"corrupted")
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "quarantine" in capsys.readouterr().err
        assert not entry.exists()
        assert repo.evidence() is None

    def test_run_denies_network_and_pins_uv_environment(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        allow_fixture_binaries: None,
    ) -> None:
        # Criterion 8: the child observes the three uv controls and cannot
        # reach the network. The child's own exit code is the probe: 0 only
        # when every control is present and the connect attempt is denied.
        probe = (
            "import os, socket, sys\n"
            "controls = (\n"
            "    os.environ.get('UV_NO_SYNC') == '1'\n"
            "    and os.environ.get('UV_OFFLINE') == '1'\n"
            "    and bool(os.environ.get('UV_PROJECT_ENVIRONMENT'))\n"
            "    and os.environ.get('VIRTUAL_ENV') == "
            "os.environ.get('UV_PROJECT_ENVIRONMENT')\n"
            ")\n"
            "denied = False\n"
            "s = socket.socket()\n"
            "s.settimeout(5)\n"
            "try:\n"
            "    s.connect(('1.1.1.1', 443))\n"
            "except OSError:\n"
            "    denied = True\n"
            "sys.exit(0 if controls and denied else 6)\n"
        )
        command = ["uv", "run", "--no-project", "python", "-c", probe]
        repo = make_repo(tmp_path, dependency=True, command=command)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)
        assert run(repo, command, monkeypatch) == 0
        evidence = repo.evidence()
        assert evidence is not None
        assert evidence[0]["exit_code"] == 0

    def test_suite_freeze_refuses_an_unapproved_dependency_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        command = ["uv", "run", "pytest", "--junitxml=report.xml"]
        repo = make_repo(tmp_path, dependency=True, command=command)
        load_store(repo)
        record_derivation(repo)

        assert invoke(
            repo,
            [
                "suite",
                "freeze",
                "--artifact",
                "report.xml",
                "--output",
                "suite_manifest.json",
                "--store",
                str(repo.store),
                "--",
                *command,
            ],
            monkeypatch,
        ) == 2
        assert "approv" in capsys.readouterr().err.lower()
        assert not (repo.root / "suite_manifest.json").exists()

    def test_suite_freeze_uses_the_provisioned_offline_denial_boundary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        allow_fixture_binaries: None,
    ) -> None:
        import ranex.cli.main as cli

        command = ["uv", "run", "pytest", "--junitxml=report.xml"]
        repo = make_repo(tmp_path, dependency=True, command=command)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)

        real_run = subprocess.run
        boundary_seen = False

        def observe_boundary(*arguments, **kwargs):
            nonlocal boundary_seen
            if kwargs.get("preexec_fn") is None:
                return real_run(*arguments, **kwargs)
            boundary_seen = True
            assert kwargs["preexec_fn"] is cli._deny_network
            environment = kwargs["env"]
            assert environment["UV_NO_SYNC"] == "1"
            assert environment["UV_OFFLINE"] == "1"
            assert environment["UV_NO_CONFIG"] == "1"
            assert environment["UV_FROZEN"] == "1"
            dependency_root = Path(environment["UV_PROJECT_ENVIRONMENT"])
            assert Path(environment["VIRTUAL_ENV"]) == dependency_root
            assert stat.S_IMODE(dependency_root.stat().st_mode) & 0o222 == 0
            (Path(kwargs["cwd"]) / "report.xml").write_text(
                '<testsuites><testsuite><testcase '
                'classname="tests.test_sample" name="test_one" />'
                '</testsuite></testsuites>',
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(arguments[0], 0)

        monkeypatch.setattr("ranex.cli.main.subprocess.run", observe_boundary)
        assert invoke(
            repo,
            [
                "suite",
                "freeze",
                "--artifact",
                "report.xml",
                "--output",
                "suite_manifest.json",
                "--store",
                str(repo.store),
                "--",
                *command,
            ],
            monkeypatch,
        ) == 0
        assert boundary_seen
        assert json.loads((repo.root / "suite_manifest.json").read_text()) == {
            "suite": ["tests/test_sample.py::test_one"],
            "expected_skips": {},
        }

    def test_dependency_root_rejects_writes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        allow_fixture_binaries: None,
    ) -> None:
        # Criterion 7 / s.p. 13: the assembled root is read-only before spawn;
        # a plain write attempt fails inside the run, and the store entry the
        # root was built from is untouched afterwards.
        probe = (
            "import os, sys, fakepkg\n"
            "root = os.environ['UV_PROJECT_ENVIRONMENT']\n"
            "target = os.path.join(root, 'planted.txt')\n"
            "try:\n"
            "    open(target, 'w').write('x')\n"
            "except OSError:\n"
            "    sys.exit(0)\n"
            "sys.exit(7)\n"
        )
        command = ["uv", "run", "--no-project", "python", "-c", probe]
        repo = make_repo(tmp_path, dependency=True, command=command)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)
        assert run(repo, command, monkeypatch) == 0
        assert (repo.store / "sha256" / sha256(FAKEPKG_WHEEL)).read_bytes() == (
            FAKEPKG_WHEEL
        )

    def test_hostile_ancestor_venv_cannot_capture_the_approved_package_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        allow_fixture_binaries: None,
    ) -> None:
        """An ancestor environment cannot displace the sealed approved root."""

        hostile_parent = tmp_path / "hostile-ancestor"
        hostile_parent.mkdir()
        hostile_environment = hostile_parent / ".venv"
        subprocess.run(
            [str(REAL_UV), "venv", "--python", sys.executable, str(hostile_environment)],
            check=True,
            capture_output=True,
            text=True,
            env={
                "PATH": "/usr/bin:/bin",
                "HOME": str(tmp_path / "hostile-home"),
                "UV_NO_CONFIG": "1",
                "UV_CACHE_DIR": str(tmp_path / "hostile-cache"),
                "UV_PYTHON_DOWNLOADS": "never",
                "UV_PROJECT_ENVIRONMENT": str(hostile_environment),
                "VIRTUAL_ENV": str(hostile_environment),
            },
        )
        site_packages = next(hostile_environment.glob("lib/python*/site-packages"))
        hostile_package = site_packages / "fakepkg"
        hostile_package.mkdir()
        (hostile_package / "__init__.py").write_text("VALUE = -1\n")

        def materialisation_below_hostile_ancestor(_repository_root: Path) -> Path:
            root = hostile_parent / "ranex-subject-hostile"
            root.mkdir()
            return root

        monkeypatch.setattr(
            "ranex.cli.subject._materialisation_root",
            materialisation_below_hostile_ancestor,
        )
        probe = (
            "import os, pathlib, sys, fakepkg\n"
            "approved = pathlib.Path(os.environ['UV_PROJECT_ENVIRONMENT']).resolve()\n"
            "active = pathlib.Path(os.environ['VIRTUAL_ENV']).resolve()\n"
            "prefix = pathlib.Path(sys.prefix).resolve()\n"
            "sys.exit(0 if fakepkg.VALUE == 42 and active == approved == prefix else 9)\n"
        )
        command = ["uv", "run", "--no-project", "python", "-c", probe]
        repo = make_repo(tmp_path, dependency=True, command=command)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)

        assert run(repo, command, monkeypatch) == 0


class TestSpawnFailure:
    def test_a_child_that_cannot_be_started_is_a_refusal_not_a_verdict(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
        allow_fixture_binaries: None,
    ) -> None:
        # A provisioned run asks the kernel for a fresh user and network
        # namespace, and a host that refuses them fails the spawn itself.
        # That must surface as a refusal with no evidence — never as a
        # command that "ran" and produced an exit code nobody observed.
        repo = make_repo(tmp_path, dependency=True, command=RUN_COMMAND)
        load_store(repo)
        record_derivation(repo)
        record_approval(repo)

        real = subprocess.run

        def refuse(*args, **kwargs):
            if kwargs.get("preexec_fn") is not None:
                raise OSError("unprivileged user namespaces are disabled")
            return real(*args, **kwargs)

        monkeypatch.setattr("ranex.cli.main.subprocess.run", refuse)
        assert run(repo, RUN_COMMAND, monkeypatch) == 2
        assert "cannot run" in capsys.readouterr().err
        assert repo.evidence() is None
