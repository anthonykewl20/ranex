"""SLICE-002 — `keygen` must not be able to put a private key in the tree.

Written before the implementation and required to fail first.

This is the criterion that adversarial review caught as unsatisfiable in the
first draft of the spec. The slice's premise is that private keys never enter
the repository, but the mechanism was only "write to the path in
$RANEX_SIGNING_KEY". An environment variable pointing inward would be obeyed,
and the key committed — defeating the entire slice while every other test
passed.

Confinement here is the inverse of `resolve_within_repository`: that refuses
paths *outside* the repository, this refuses paths *inside* it.

    ranex keygen --producer <id>       # writes $RANEX_SIGNING_KEY, 0600
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from ranex.cli.main import governed_repository_root, main

EXIT_USAGE = 2


@pytest.fixture()
def repo_root() -> Path:
    return governed_repository_root()


def test_refuses_to_write_inside_the_repository(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
) -> None:
    target = repo_root / "governance" / "worker.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(target))

    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE
    assert not target.exists()


def test_refuses_to_write_inside_dot_git(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
) -> None:
    target = repo_root / ".git" / "worker.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(target))

    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE
    assert not target.exists()


def test_refuses_when_the_variable_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE


def test_refuses_a_relative_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A relative path resolves against whatever cwd happens to be, which may
    well be the repository."""

    monkeypatch.setenv("RANEX_SIGNING_KEY", "worker.key")
    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE


def test_refuses_a_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(tmp_path))
    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE


def test_refuses_to_overwrite_an_existing_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Silently replacing a key would orphan every record it ever signed."""

    target = tmp_path / "worker.key"
    target.write_text("existing\n", encoding="utf-8")
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(target))

    assert main(["keygen", "--producer", "worker"]) == EXIT_USAGE
    assert target.read_text(encoding="utf-8") == "existing\n"


def test_writes_outside_the_repository_with_owner_only_permissions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "worker.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(target))

    assert main(["keygen", "--producer", "worker"]) == 0
    assert target.exists()

    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode == 0o600, f"private key is {oct(mode)}, must be 0o600"

    # And it must print the line to paste into the committed keyring, or the
    # operator has a key nobody trusts and no obvious way to register it.
    printed = capsys.readouterr().out
    assert "worker" in printed
    assert "ed25519:" in printed
