from __future__ import annotations

import inspect
from pathlib import Path

import pytest


@pytest.mark.parametrize("bad", [1.5, 2**53, -(2**53), "\U0001f600"])
def test_publication_validator_refuses_cross_language_values(bad: object) -> None:
    from ranex.governed_execution.verdict_publication import validate_publication_value

    with pytest.raises(ValueError):
        validate_publication_value({"value": bad})


def test_publication_validator_refuses_non_bmp_keys() -> None:
    from ranex.governed_execution.verdict_publication import validate_publication_value

    with pytest.raises(ValueError):
        validate_publication_value({"\U0001f600": "value"})


def test_shared_atomic_writer_is_used_by_both_callers() -> None:
    from ranex.cli import host_confinement
    from ranex.governed_execution import verdict_publication

    assert "atomic_writer" in inspect.getsource(host_confinement)
    assert "atomic_writer" in inspect.getsource(verdict_publication)
    assert "host_confinement" not in inspect.getsource(verdict_publication)


def test_atomic_publication_preserves_previous_record_on_failure(tmp_path: Path, monkeypatch) -> None:
    from ranex.foundation import atomic_writer

    target = tmp_path / "verdict.json"
    target.write_bytes(b"previous")
    monkeypatch.setattr(atomic_writer.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        atomic_writer.write_atomic(target, b"new", root=tmp_path)
    assert target.read_bytes() == b"previous"
    assert not list(tmp_path.glob(".verdict.json.*"))


def test_atomic_writer_refuses_intermediate_symlink_escape(tmp_path: Path) -> None:
    from ranex.foundation import atomic_writer

    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "publication").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        atomic_writer.write_atomic(
            root / "publication" / "verdict.json", b"escaped", root=root
        )

    assert not (outside / "verdict.json").exists()


def test_atomic_writer_forces_exact_read_only_mode_despite_umask(tmp_path: Path) -> None:
    import os
    import stat

    from ranex.foundation import atomic_writer

    target = tmp_path / "verdict.json"
    previous = os.umask(0o777)
    try:
        atomic_writer.write_atomic(target, b"record", root=tmp_path)
    finally:
        os.umask(previous)

    assert stat.S_IMODE(target.stat().st_mode) == 0o444
