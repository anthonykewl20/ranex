from __future__ import annotations

from pathlib import Path

import pytest


def test_verdict_private_key_inside_governed_repository_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ranex.cli import main

    root = tmp_path / "repo"
    root.mkdir()
    key = root / "verdict.key"
    key.write_text("private", encoding="utf-8")
    key.chmod(0o600)
    monkeypatch.setenv(main.VERDICT_SIGNING_KEY_VARIABLE, str(key))
    monkeypatch.setattr(main, "committable_into", lambda path, governed: True)

    with pytest.raises(ValueError, match="inside.*repository|committable"):
        main.private_signing_key(root, variable=main.VERDICT_SIGNING_KEY_VARIABLE)


def test_verdict_private_key_readable_by_group_or_other_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ranex.cli import main

    root = tmp_path / "repo"
    root.mkdir()
    key = tmp_path / "verdict.key"
    key.write_text("private", encoding="utf-8")
    key.chmod(0o644)
    monkeypatch.setenv(main.VERDICT_SIGNING_KEY_VARIABLE, str(key))
    monkeypatch.setattr(main, "committable_into", lambda path, governed: False)

    with pytest.raises(ValueError, match="readable by group or other"):
        main.private_signing_key(root, variable=main.VERDICT_SIGNING_KEY_VARIABLE)
