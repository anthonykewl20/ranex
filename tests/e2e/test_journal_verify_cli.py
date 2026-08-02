"""The operator-facing journal verifier must never bless absence."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ranex.cli.main import main


@pytest.fixture()
def repository(tmp_path: Path) -> Path:
    path = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def test_verify_refuses_a_missing_journal_without_creating_it(
    repository: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Deleting the record is not a valid empty chain."""

    missing = repository / "never-existed.sqlite3"
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repository)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repository.resolve()
        )
        assert main(
            [
                "journal",
                "verify",
                "--repository",
                ".",
                "--journal",
                missing.name,
            ]
        ) == 2

    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert "PASS" not in captured.out
    assert not missing.exists()
