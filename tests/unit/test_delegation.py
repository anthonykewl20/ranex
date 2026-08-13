"""Unit tests for delegated execution API pins."""

from __future__ import annotations

import importlib
import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def delegation():
    try:
        return importlib.import_module("ranex.cli.delegation")
    except ModuleNotFoundError as error:
        raise AssertionError("delegation module is not yet implemented") from error


def probe_environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
    }


def test_model_credential_variable_is_pinned() -> None:
    module = delegation()
    assert module.MODEL_CREDENTIAL_VARIABLE == "OPENROUTER_API_KEY"


def test_exec_environment_holds_signing_key_uses_proc_environ(tmp_path: Path) -> None:
    if "MUTANT_UNDER_TEST" in os.environ:
        # The probe subprocess imports the copied tree, whose trampoline cannot
        # initialise mutmut's runtime outside its runner. The same property is
        # asserted in-process above, so mutation pressure is not lost.
        pytest.skip("probe subprocess cannot run the mutmut-trampolined tree")
    if b"RANEX_SIGNING_KEY" in Path("/proc/self/environ").read_bytes():
        pytest.skip("in-process check is invalid when parent process already owns RANEX_SIGNING_KEY")

    os.environ["RANEX_SIGNING_KEY"] = str(tmp_path / "proc-key.txt")
    try:
        module = delegation()
        assert module.exec_environment_holds_signing_key() is False
    finally:
        os.environ.pop("RANEX_SIGNING_KEY", None)

    probe = tmp_path / "check_proc_environment.py"
    probe.write_text(
        textwrap.dedent(
            """\
            import os
            os.environ.pop("RANEX_SIGNING_KEY", None)
            from ranex.cli.delegation import exec_environment_holds_signing_key

            print(exec_environment_holds_signing_key())
            """
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(probe)],
        check=False,
        capture_output=True,
        text=True,
        env={**probe_environment(), "RANEX_SIGNING_KEY": "/tmp/ranex-signing-key-for-proc-test"},
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "True"


def test_exec_environment_holds_verdict_signing_key_uses_proc_environ(tmp_path: Path) -> None:
    if "MUTANT_UNDER_TEST" in os.environ:
        # The probe subprocess imports the copied tree, whose trampoline cannot
        # initialise mutmut's runtime outside its runner. The same property is
        # asserted in-process above, so mutation pressure is not lost.
        pytest.skip("probe subprocess cannot run the mutmut-trampolined tree")
    if b"RANEX_VERDICT_SIGNING_KEY" in Path("/proc/self/environ").read_bytes():
        pytest.skip(
            "in-process check is invalid when parent process already owns "
            "RANEX_VERDICT_SIGNING_KEY"
        )

    os.environ["RANEX_VERDICT_SIGNING_KEY"] = str(tmp_path / "proc-verdict-key.txt")
    try:
        module = delegation()
        assert module.exec_environment_holds_signing_key() is False
    finally:
        os.environ.pop("RANEX_VERDICT_SIGNING_KEY", None)

    probe = tmp_path / "check_proc_verdict_environment.py"
    probe.write_text(
        textwrap.dedent(
            """\
            import os
            os.environ.pop("RANEX_VERDICT_SIGNING_KEY", None)
            from ranex.cli.delegation import exec_environment_holds_signing_key

            print(exec_environment_holds_signing_key())
            """
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(probe)],
        check=False,
        capture_output=True,
        text=True,
        env={
            **probe_environment(),
            "RANEX_VERDICT_SIGNING_KEY": "/tmp/ranex-verdict-signing-key-for-proc-test",
        },
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "True"


def test_run_harness_timeout_reaps_process_group(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = delegation()

    class FakeProcess:
        pid = 77

        def __enter__(self) -> FakeProcess:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)

        def wait(self, timeout: float | None = None) -> int:
            return 0

    called = {
        "killed": False,
    }

    def fake_killpg(group: int, signum: int) -> None:
        called["killed"] = True
        called["group"] = group
        called["signum"] = signum

    monkeypatch.setattr(module.subprocess, "Popen", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(module.os, "getpgid", lambda _pid: 77)
    monkeypatch.setattr(module.os, "killpg", fake_killpg)

    with pytest.raises(subprocess.TimeoutExpired):
        module._run_harness(
            harness=tmp_path / "harness.sh",
            worktree=tmp_path / "worktree",
            model="ranex-noop/noop",
            prompt="perform work then emit",
            timeout=1,
            environment=module.execute_environment(
                {
                    "PATH": "/usr/bin:/bin",
                    "OPENROUTER_API_KEY": "openrouter-key",
                },
                task_id="T-8",
                emit="/tmp/emit.jsonl",
                home=str(tmp_path / "home"),
            ),
        )

    assert called["killed"] is True
    assert called["group"] == 77
    assert called["signum"] == signal.SIGKILL


def test_run_harness_timeout_wait_fallback_on_unresponsive_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = delegation()

    class FakeProcess:
        pid = 88
        wait_calls = 0
        killed = False

        def __enter__(self) -> FakeProcess:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)

        def kill(self) -> None:
            self.killed = True

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)
            return 0

    process = FakeProcess()

    monkeypatch.setattr(module.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(module.os, "getpgid", lambda _pid: 88)
    monkeypatch.setattr(module.os, "killpg", lambda _group, _signum: None)

    with pytest.raises(subprocess.TimeoutExpired):
        module._run_harness(
            harness=tmp_path / "harness.sh",
            worktree=tmp_path / "worktree",
            model="ranex-noop/noop",
            prompt="perform work then emit",
            timeout=1,
            environment=module.execute_environment(
                {
                    "PATH": "/usr/bin:/bin",
                    "OPENROUTER_API_KEY": "openrouter-key",
                },
                task_id="T-8",
                emit="/tmp/emit.jsonl",
                home=str(tmp_path / "home"),
            ),
        )

    assert process.killed is True
    assert process.wait_calls >= 2


def test_run_harness_timeout_no_process_group_still_reaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = delegation()

    class FakeProcess:
        pid = 99
        wait_calls = 0

        def __enter__(self) -> FakeProcess:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            return 0

    process = FakeProcess()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(
        module.os,
        "getpgid",
        lambda _pid: (_ for _ in ()).throw(ProcessLookupError()),
    )

    with pytest.raises(subprocess.TimeoutExpired):
        module._run_harness(
            harness=tmp_path / "harness.sh",
            worktree=tmp_path / "worktree",
            model="ranex-noop/noop",
            prompt="perform work then emit",
            timeout=1,
            environment=module.execute_environment(
                {
                    "PATH": "/usr/bin:/bin",
                    "OPENROUTER_API_KEY": "openrouter-key",
                },
                task_id="T-8",
                emit="/tmp/emit.jsonl",
                home=str(tmp_path / "home"),
            ),
        )

    assert process.wait_calls == 1


def test_execute_environment_only_includes_the_bridge_variables() -> None:
    module = delegation()
    # No RANEX_SIGNING_KEY here: its presence is a refusal, pinned by
    # test_execute_environment_rejects_signing_key_in_ambient. This case pins
    # the other half — that an ambient variable nobody asked for is dropped.
    ambient = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/tmp/ignored-home",
        "OPENROUTER_API_KEY": "token-present",
        "UNRELATED": "ignore-me",
    }
    environment = module.execute_environment(
        ambient,
        task_id="T-008",
        emit="/tmp/emit.jsonl",
        home="/tmp/delegation-home",
    )
    assert set(environment) == {
        "PATH",
        "HOME",
        "RANEX_TASK_ID",
        "RANEX_EMIT",
        "OPENROUTER_API_KEY",
    }
    assert environment["RANEX_TASK_ID"] == "T-008"
    assert environment["RANEX_EMIT"] == "/tmp/emit.jsonl"
    assert environment["HOME"] == "/tmp/delegation-home"
    assert environment["OPENROUTER_API_KEY"] == "token-present"
    assert "RANEX_VERDICT_SIGNING_KEY" not in environment
    assert "RANEX_VERDICT_DIR" not in environment


def test_execute_environment_rejects_signing_key_in_ambient() -> None:
    module = delegation()
    with pytest.raises(ValueError, match=r"RANEX_SIGNING_KEY"):
        module.execute_environment(
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/delegation-home",
                "RANEX_SIGNING_KEY": "/tmp/key",
                "OPENROUTER_API_KEY": "token-present",
            },
            task_id="T-008",
            emit="/tmp/emit.jsonl",
            home="/tmp/delegation-home",
        )


def test_execute_environment_rejects_verdict_signing_key_in_ambient() -> None:
    module = delegation()
    with pytest.raises(ValueError, match=r"RANEX_VERDICT_SIGNING_KEY"):
        module.execute_environment(
            {"PATH": "/usr/bin:/bin", "OPENROUTER_API_KEY": "token-present",
             "RANEX_VERDICT_SIGNING_KEY": "/tmp/verdict-key"},
            task_id="T-008", emit="/tmp/emit.jsonl", home="/tmp/home",
        )


def test_execute_environment_rejects_a_missing_model_credential() -> None:
    module = delegation()
    with pytest.raises(ValueError, match=r"OPENROUTER_API_KEY"):
        module.execute_environment(
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/delegation-home",
            },
            task_id="T-008",
            emit="/tmp/emit.jsonl",
            home="/tmp/delegation-home",
        )
