"""Guards for the dogfood/oss_bench harness — argv parsing, path isolation,
timeout classification, and proof-pile harness-fault accounting."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOGFOOD = REPO_ROOT / "tools" / "dogfood"
sys.path.insert(0, str(DOGFOOD))
sys.path.insert(0, str(DOGFOOD / "oss_bench"))
sys.path.insert(0, str(DOGFOOD / "trainer"))

from cmdparse import node_ids_from_entries, parse_cmd, pinned_argv  # noqa: E402
from proofs import (  # noqa: E402
    _is_false_block,
    _is_false_pass,
    harness_fault_reason,
    summary,
)
from trainer.main import _is_timeout  # noqa: E402
from trainer.variants import first_hunk_patch  # noqa: E402


def test_parse_cmd_does_not_use_argv3() -> None:
    env, argv, nodes = parse_cmd(
        "PYTHONPATH=. python -m pytest -c /dev/null -p no:cacheprovider "
        "oss_tests.py::test_book_vs_physical -q"
    )
    assert env == ["PYTHONPATH=."]
    assert "pytest" in argv
    assert nodes == ["oss_tests.py::test_book_vs_physical"]
    import shlex
    raw = shlex.split(
        "PYTHONPATH=. python -m pytest -c /dev/null -p no:cacheprovider "
        "oss_tests.py::test_book_vs_physical -q"
    )
    assert raw[3] == "pytest"  # the trap the old harness fell into


def test_parse_cmd_v1_grammar() -> None:
    _env, _argv, nodes = parse_cmd(
        "python -m pytest test_pagination.py::test_is_after_is_strict -q"
    )
    assert nodes == ["test_pagination.py::test_is_after_is_strict"]


def test_node_ids_from_entries_refuses_cmd_without_nodes() -> None:
    with pytest.raises(AssertionError, match="no test node ids"):
        node_ids_from_entries([{"cmd": "pytest -q"}])


def test_pinned_argv_rewrites_python() -> None:
    assert pinned_argv(["python", "-m", "pytest"])[0] == "/usr/bin/python3"
    assert pinned_argv(["/usr/bin/python3", "-m", "pytest"])[0] == "/usr/bin/python3"


def test_harness_fault_kernel_journal_is_not_a_false_block() -> None:
    entry = {
        "kind": "run",
        "ground_truth_functional": 1.0,
        "ranex_gate": {
            "gate_verdict": "FAIL",
            "run_exit": 2,
            "run_error": "points at no file: /tmp/x",
            "journal_output": (
                "PASS  journal=/home/soultransit/devtony/ranex/"
                "governance/journal.sqlite3  chain=verified"
            ),
            "run_command": "ranex run -- pytest pytest pytest",
        },
    }
    assert harness_fault_reason(entry)
    assert not _is_false_block(entry)
    assert not _is_false_pass(entry)


def test_summary_excludes_committed_harness_faults() -> None:
    report = summary()
    assert report["false_passes"] == 0
    # 0017 and 0018 stored false_block=true; they judged the kernel journal.
    assert report["false_blocks"] == 0
    assert report["harness_faults"] >= 2


def test_timeout_detection_uses_the_exception_type() -> None:
    try:
        subprocess.run(["sleep", "2"], timeout=0.05)
    except subprocess.TimeoutExpired as exc:
        assert _is_timeout(exc)
        assert "TimeoutExpired" not in str(exc)
        return
    raise AssertionError("sleep did not time out")


def test_first_hunk_patch_withholds_later_files(tmp_path: Path) -> None:
    raw = (
        b"diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1 +1 @@\n-a\n+b\n"
        b"diff --git a/g b/g\n--- a/g\n+++ b/g\n@@ -1 +1 @@\n-x\n+y\n"
    )
    patch = tmp_path / "gold.diff"
    patch.write_bytes(raw)
    partial = first_hunk_patch(patch, tmp_path)
    assert partial is not None
    payload = partial.read_bytes()
    assert b"diff --git a/f b/f" in payload
    assert b"diff --git a/g b/g" not in payload


def test_first_hunk_patch_skips_true_single_hunk(tmp_path: Path) -> None:
    raw = b"diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1 +1 @@\n-a\n+b\n"
    patch = tmp_path / "gold.diff"
    patch.write_bytes(raw)
    assert first_hunk_patch(patch, tmp_path) is None


def test_ranex_exports_absolute_key_and_pythonpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_run(*_args: object, **kwargs: object) -> object:
        captured["env"] = kwargs["env"]
        captured["cwd"] = kwargs["cwd"]

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Result()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)
    from two_arm import _ranex

    repo = tmp_path / "nested" / "repo"
    repo.mkdir(parents=True)
    (repo / "src").mkdir()
    key = tmp_path / "nested" / "keys" / "k"
    key.parent.mkdir()
    key.write_text("x")
    _ranex(Path("nested/repo"), "nested/keys/k", "--help")
    env = captured["env"]
    assert isinstance(env, dict)
    key_env = env["RANEX_SIGNING_KEY"]
    py_env = env["PYTHONPATH"]
    assert Path(key_env).is_absolute()
    assert Path(py_env).is_absolute()
    assert "nested/repo/nested/keys" not in key_env
    assert Path(key_env) == key.resolve()
    assert Path(py_env) == (repo / "src").resolve()
