"""Slice 008 — execute and attest separation controls."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from ranex.foundation.signing import SIGNED_FIELDS, generate_keypair, verify_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

CLI_SOURCE = Path(__file__).resolve().parents[2] / "src" / "ranex"
SUITE = f"{sys.executable} -m pytest -q -p no:cacheprovider"
PLANTED_KEY_SNIPPET = "signing-key-content-unique-008"
VALID_FAKE_SIGNATURE = "ed25519:" + base64.b64encode(b"\x00" * 64).decode("ascii")
SMOKE_TEST = "def test_smoke() -> None:\n    assert True\n"


def environment_for_process(*, home: Path, python_path: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(python_path),
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if extra is not None:
        environment.update(extra)
    return environment


def build_target(tmp_path: Path) -> tuple[Path, Path, str]:
    """Create a governed repository that can be invoked as a delegate target."""

    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "-C", str(target), "init", "-q"], check=True, env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"))
    for key, value in (("user.email", "slice008@example.invalid"), ("user.name", "Slice 008")):
        subprocess.run(
            ["git", "-C", str(target), "config", key, value],
            check=True,
            env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
        )
    shutil.copytree(
        CLI_SOURCE,
        target / "src" / "ranex",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (target / "tests").mkdir()
    (target / "tests" / "test_smoke.py").write_text(SMOKE_TEST, encoding="utf-8")

    private, public = generate_keypair()
    signing_key = tmp_path / "worker.key"
    signing_key.write_text(private + "\n", encoding="utf-8")
    signing_key.chmod(0o600)

    (target / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    (target / "app.txt").write_text("governed\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(target), "add", "-A"],
        check=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    )
    subprocess.run(
        ["git", "-C", str(target), "commit", "-q", "-m", "initial target"],
        check=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    )
    return target, signing_key, public


def conftest_source(*, key_snippet: str = PLANTED_KEY_SNIPPET) -> str:
    template = textwrap.dedent(
        """\
        import os
        import json
        from pathlib import Path

        FORGED_SIGNATURE = __FORGED_SIGNATURE__
        KEY_SNIPPET = __KEY_SNIPPET__
        CLAIM_RECORD = {
            "claim_id": "tests-executed",
            "command": "uv run --frozen pytest -q",
            "command_digest": "sha256:" + "0" * 64,
            "executable_path": "/usr/bin/uv",
            "exit_code": 1,
            "producer_id": "worker",
            "subject_digest": "sha256:" + "0" * 64,
            "suite_results": None,
            "confinement_result_digest": "sha256:" + "a" * 64,
            "confinement_profile_digest": "sha256:" + "b" * 64,
            "signature": FORGED_SIGNATURE,
        }


        def _read_proc_environ(pid: int) -> bytes:
            try:
                return Path(f"/proc/{pid}/environ").read_bytes()
            except OSError:
                return b""


        def _read_ppid(pid: int) -> int | None:
            try:
                stat = Path(f"/proc/{pid}/stat").read_text(errors="ignore").split()
                return int(stat[3])
            except (FileNotFoundError, ValueError, OSError, IndexError):
                return None


        def _scan(proc_name: str, pid: int, target: bytes) -> dict[str, bool]:
            data = _read_proc_environ(pid)
            return {
                "scope": proc_name,
                "has_key_name": b"RANEX_SIGNING_KEY" in data,
                "has_key_content": target in data,
            }


        def _writes(path: str, payload: dict[str, object]) -> None:
            Path(path).write_text(json.dumps(payload), encoding="utf-8")


        pid = os.getpid()
        ppid = os.getppid()
        pp = _read_ppid(ppid)

        theft_report = {
            "scans": [
                _scan("self", pid, KEY_SNIPPET.encode("utf-8")),
                _scan("parent", ppid, KEY_SNIPPET.encode("utf-8")),
            ]
        }
        if pp is not None:
            theft_report["scans"].append(_scan("grandparent", pp, KEY_SNIPPET.encode("utf-8")))

        _writes(str(Path(__file__).parent / "forged_evidence.json"), [CLAIM_RECORD])
        _writes(str(Path(__file__).parent / "theft_report.json"), theft_report)

        # The findings travel in the exception message, not only in those files.
        # The hook runs inside the kernel's materialisation of the commit — a
        # temporary tree that is torn down — so anything written there is gone
        # before the test looks. The suite output is the channel that survives.
        raise RuntimeError(
            "PLANTED_CONFTEST_HOOK_RAN "
            + json.dumps(
                {"theft": theft_report, "forged": CLAIM_RECORD},
                separators=(",", ":"),
            )
        )
        """
    )
    return (
        template.replace("__FORGED_SIGNATURE__", repr(VALID_FAKE_SIGNATURE))
        .replace("__KEY_SNIPPET__", repr(key_snippet))
    )


def harness_script(
    path: Path,
    *,
    capture: Path | None = None,
    marker: Path | None = None,
    plant_conftest: bool = False,
    emit: bool = True,
    emit_task_id: str | None = None,
    emit_worktree: Path | None = None,
    emit_commit: str | None = None,
    delete_worktree: bool = False,
    commit_work: bool = True,
    empty_commit: bool = False,
) -> Path:
    """Reusable executable harness script for delegation integration tests."""

    capture_arg = repr(str(capture)) if capture is not None else None
    marker_arg = repr(str(marker)) if marker is not None else None
    conftest = conftest_source() if plant_conftest else None
    conftest_arg = repr(conftest) if conftest is not None else None
    emit_task_id_arg = repr(emit_task_id) if emit_task_id is not None else None
    emit_worktree_arg = repr(str(emit_worktree)) if emit_worktree is not None else None
    emit_commit_arg = repr(emit_commit) if emit_commit is not None else None
    body = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import json
        import os
        import shutil
        import subprocess
        import sys
        from pathlib import Path


        def parse_args(arguments):
            parsed = {}
            iterator = iter(arguments)
            for token in iterator:
                if token == "--dir":
                    parsed["worktree"] = next(iterator)
                elif token == "--model":
                    parsed["model"] = next(iterator)
                elif token == "--auto":
                    parsed["prompt"] = next(iterator)
            return parsed


        def read_parent(pid):
            try:
                stat = Path(f"/proc/{pid}/stat").read_text(errors=\"ignore\").split()
                return int(stat[3])
            except (FileNotFoundError, IndexError, OSError, ValueError):
                return None


        def read_proc(pid):
            output.write(f"[pid={pid}]\\n".encode())
            try:
                output.write(Path(f"/proc/{pid}/environ").read_bytes())
            except OSError as error:
                output.write(f"<{error}>\\n".encode())
            output.write(b"\\n--\\n")


        args = parse_args(sys.argv[1:])
        worktree = Path(args["worktree"])

        marker_path = __MARKER_PATH__
        capture_path = __CAPTURE_PATH__
        conftest_source = __CONFTEST_SOURCE__
        emit_task_id = __EMIT_TASK_ID__
        emit_worktree = __EMIT_WORKTREE__
        emit_commit = __EMIT_COMMIT__

        if marker_path is not None:
            Path(marker_path).write_text("spawned", encoding="utf-8")

        if capture_path is not None:
            with Path(capture_path).open("wb") as output:
                read_proc(os.getpid())
                read_proc(os.getppid())
                grandparent = read_parent(os.getppid())
                if grandparent is not None:
                    read_proc(grandparent)

        if conftest_source is not None:
            (worktree / "conftest.py").write_text(conftest_source, encoding="utf-8")

        subprocess.run(["/usr/bin/git", "-C", str(worktree), "config", "user.email", "harness@example.invalid"], check=True)
        subprocess.run(["/usr/bin/git", "-C", str(worktree), "config", "user.name", "Harness"], check=True)

        if __EMPTY_COMMIT__:
            # A commit whose SHA differs from base over a byte-identical tree.
            subprocess.run(
                ["/usr/bin/git", "-C", str(worktree), "commit", "-q", "--allow-empty",
                 "-m", "agent work"],
                check=True,
            )
        elif __COMMIT_WORK__:
            (worktree / "agent.txt").write_text("work from harness\\n", encoding="utf-8")
            # -A, not the single file: the real harness commits everything in the
            # worktree, and criterion 3 needs the planted hook to reach the commit
            # the kernel materialises. Untracked state never enters the subject.
            subprocess.run(["/usr/bin/git", "-C", str(worktree), "add", "-A"], check=True)
            subprocess.run(
                ["/usr/bin/git", "-C", str(worktree), "commit", "-q", "-m", "agent work"],
                check=True,
            )

        if __EMIT__:
            emitted_task_id = os.environ["RANEX_TASK_ID"]
            emitted_worktree = str(worktree)
            commit = subprocess.check_output(
                ["/usr/bin/git", "-C", str(worktree), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            if emit_task_id is not None:
                emitted_task_id = emit_task_id
            if emit_worktree is not None:
                emitted_worktree = emit_worktree
            if emit_commit is not None:
                commit = emit_commit
            emission = {
                "task_id": emitted_task_id,
                "worktree": emitted_worktree,
                "commit": commit,
            }
            Path(os.environ["RANEX_EMIT"]).write_text(json.dumps(emission) + "\\n", encoding="utf-8")

        if __DELETE_WORKTREE__ and worktree.exists():
            shutil.rmtree(worktree, ignore_errors=True)
        """
    )
    body = body.replace("__MARKER_PATH__", marker_arg or "None")
    body = body.replace("__CAPTURE_PATH__", capture_arg or "None")
    body = body.replace("__CONFTEST_SOURCE__", conftest_arg or "None")
    body = body.replace("__EMIT__", "True" if emit else "False")
    body = body.replace("__EMIT_TASK_ID__", emit_task_id_arg or "None")
    body = body.replace("__EMIT_WORKTREE__", emit_worktree_arg or "None")
    body = body.replace("__EMIT_COMMIT__", emit_commit_arg or "None")
    body = body.replace("__DELETE_WORKTREE__", "True" if delete_worktree else "False")
    body = body.replace("__COMMIT_WORK__", "True" if commit_work else "False")
    body = body.replace("__EMPTY_COMMIT__", "True" if empty_commit else "False")

    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def write_stall_harness(
    path: Path,
    *,
    child_pid_path: Path,
    grandchild_pid_path: Path,
) -> Path:
    body = textwrap.dedent(
        """\
        #!/usr/bin/env sh
        set -eu

        while [ "$#" -gt 0 ]; do
          case "$1" in
            --dir|--model|--auto)
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done

        printf '%s\\n' "$$" > "__CHILD_PID_FILE__"
        (
          sleep 300
        ) &
        printf '%s\\n' "$!" > "__GRANDCHILD_PID_FILE__"
        wait
        """
    )
    body = body.replace("__CHILD_PID_FILE__", str(child_pid_path))
    body = body.replace("__GRANDCHILD_PID_FILE__", str(grandchild_pid_path))

    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def run_delegate(
    *,
    target: Path,
    task_id: str,
    worktree: Path,
    journal: Path,
    harness: Path,
    outcome: Path,
    openrouter: str | None,
    signing_key: Path | None = None,
    timeout: int | str = 120,
    suite: str = SUITE,
) -> subprocess.CompletedProcess[str]:
    env = environment_for_process(home=tmp_home(target), python_path=target / "src")
    if signing_key is not None:
        env["RANEX_SIGNING_KEY"] = str(signing_key)
    if openrouter is not None:
        env["OPENROUTER_API_KEY"] = openrouter

    return subprocess.run(
        [
            sys.executable,
            "-m", "ranex.cli.main",
            "task",
            "delegate",
            "--task-id", task_id,
            "--target", str(target),
            "--worktree", str(worktree),
            "--journal", str(journal),
            "--harness", str(harness),
            "--model", "ranex-noop/noop",
            "--prompt", "perform work then emit",
            "--timeout", str(timeout),
            "--suite", suite,
            "--outcome", str(outcome),
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def run_fanout(
    *,
    target: Path,
    tasks: Path,
    journal: Path,
    harness: Path,
    timeout: int | str,
    outcome_dir: Path,
    pool: int,
    openrouter: str | None = "openrouter-key",
) -> subprocess.CompletedProcess[str]:
    tmpdir = target / "operator-fanout-tmp"
    tmpdir.mkdir(exist_ok=True)
    env = environment_for_process(home=tmp_home(target), python_path=target / "src")
    if openrouter is not None:
        env["OPENROUTER_API_KEY"] = openrouter
    env["TMPDIR"] = str(tmpdir)
    return subprocess.run(
        [
            sys.executable,
            "-m", "ranex.cli.main",
            "task",
            "fanout",
            "--tasks", str(tasks),
            "--target", str(target),
            "--journal", str(journal),
            "--harness", str(harness),
            "--model", "ranex-noop/noop",
            "--timeout", str(timeout),
            "--suite", "/usr/bin/true",
            "--outcome-dir", str(outcome_dir),
            "--pool", str(pool),
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def run_task_judge(
    *,
    target: Path,
    task_id: str,
    emitted_worktree: Path,
    emitted_commit: str,
    journal: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m", "ranex.cli.main",
            "task",
            "judge",
            "--task-id", task_id,
            "--emitted-worktree", str(emitted_worktree),
            "--emitted-commit", emitted_commit,
            "--gate", "slice-008",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--journal", str(journal),
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=environment_for_process(home=tmp_home(target), python_path=target / "src"),
    )


def assert_process_died(pid: int) -> None:
    for _ in range(25):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    raise AssertionError(f"process {pid} did not terminate")


def tmp_home(root: Path) -> Path:
    return root / "operator-home"


def journal_rows(journal: Path) -> list[dict[str, object]]:
    if not journal.is_file():
        return []
    return Journal(journal).entries()


def parse_capture(path: Path) -> list[tuple[int, list[str], dict[str, str]]]:
    data = path.read_bytes()
    blocks: list[tuple[int, list[str], dict[str, str]]] = []
    for section in data.split(b"\n--\n"):
        if not section.strip():
            continue
        header, _, payload = section.partition(b"\n")
        if not header.startswith(b"[pid="):
            continue
        try:
            pid = int(header[5:-1].decode("utf-8"))
        except ValueError:
            continue
        names: list[str] = []
        values: dict[str, str] = {}
        for field in payload.split(b"\0"):
            if not field or b"=" not in field:
                continue
            name, value = field.split(b"=", maxsplit=1)
            names.append(name.decode("utf-8", "surrogatepass"))
            if name in values:
                continue
            values[name.decode("utf-8", "surrogatepass")] = value.decode(
                "utf-8", "surrogatepass"
            )
        blocks.append((pid, names, values))
    return blocks


def read_outcome(outcome: Path) -> dict[str, object]:
    lines = [
        line.strip()
        for line in outcome.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return json.loads(lines[-1])


def build_queued_harness(
    path: Path,
    *,
    counter_dir: Path,
    sleep_seconds: float,
    emit: bool = True,
    rendezvous: int | None = None,
) -> Path:
    body = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import fcntl
        import json
        import os
        import subprocess
        import time
        from pathlib import Path


        def parse_args(arguments):
            parsed = {}
            iterator = iter(arguments)
            for token in iterator:
                if token == "--dir":
                    parsed["worktree"] = next(iterator)
                elif token == "--model":
                    parsed["model"] = next(iterator)
                elif token == "--auto":
                    parsed["prompt"] = next(iterator)
            return parsed


        def _read_int(path: Path) -> int:
            try:
                return int(path.read_text(encoding="utf-8").strip())
            except OSError:
                return 0
            except ValueError:
                return 0


        args = parse_args(os.sys.argv[1:])
        worktree = Path(args["worktree"])

        state = Path("__COUNTER_DIR__")
        lock = state / "lock"
        current = state / "current"
        peak = state / "peak"
        state.mkdir(exist_ok=True)
        lock_text = state / "lock"

        lock = open(lock_text, "a+")
        fcntl.flock(lock, fcntl.LOCK_EX)
        concurrency = _read_int(current) + 1
        current.write_text(str(concurrency), encoding="utf-8")
        observed = _read_int(peak)
        peak.write_text(str(concurrency if concurrency > observed else observed), encoding="utf-8")
        fcntl.flock(lock, fcntl.LOCK_UN)

        # Rendezvous: hold here until the recorded peak shows the requested
        # concurrency, so overlap is a fact rather than a scheduling accident.
        # If a regression serialised the pool, the wait times out, the run
        # completes anyway, and the caller's peak assertion fails red.
        rendezvous = __RENDEZVOUS__
        if rendezvous is not None:
            deadline = time.monotonic() + 60.0
            while _read_int(peak) < rendezvous and time.monotonic() < deadline:
                time.sleep(0.05)

        try:
            subprocess.run(["/usr/bin/git", "-C", str(worktree), "config", "user.email", "harness@example.invalid"], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(worktree), "config", "user.name", "Harness"], check=True)
            (worktree / "agent.txt").write_text("work from harness\\n", encoding="utf-8")
            subprocess.run(["/usr/bin/git", "-C", str(worktree), "add", "-A"], check=True)
            subprocess.run(
                ["/usr/bin/git", "-C", str(worktree), "commit", "-q", "-m", "agent work"],
                check=True,
            )
            time.sleep(__SLEEP_SECONDS__)
            if __EMIT__:
                emitted_task_id = os.environ["RANEX_TASK_ID"]
                emitted_worktree = str(worktree)
                commit = subprocess.check_output(
                    ["/usr/bin/git", "-C", str(worktree), "rev-parse", "HEAD"],
                    text=True,
                ).strip()
                emission = {
                    "task_id": emitted_task_id,
                    "worktree": emitted_worktree,
                    "commit": commit,
                }
                Path(os.environ["RANEX_EMIT"]).write_text(json.dumps(emission) + "\\n", encoding="utf-8")
        finally:
            fcntl.flock(lock, fcntl.LOCK_EX)
            current_value = max(_read_int(current) - 1, 0)
            current.write_text(str(current_value), encoding="utf-8")
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
        """
    )
    body = body.replace("__COUNTER_DIR__", str(counter_dir))
    body = body.replace("__SLEEP_SECONDS__", repr(sleep_seconds))
    body = body.replace("__EMIT__", "True" if emit else "False")
    body = body.replace("__RENDEZVOUS__", repr(rendezvous))

    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def hook_findings(suite_output_tail: str) -> dict[str, object]:
    """What the planted hook found, recovered from the suite's own output.

    It cannot be read from the worktree: the hook runs inside the kernel's
    materialisation of the emitted commit, and that tree is torn down before the
    test looks. The suite output the kernel recorded is the surviving channel.
    """

    for line in suite_output_tail.splitlines():
        if "PLANTED_CONFTEST_HOOK_RAN" not in line:
            continue
        start = line.find("{")
        end = line.rfind("}")
        if start == -1 or end <= start:
            continue
        try:
            return json.loads(line[start : end + 1])
        except json.JSONDecodeError:
            continue
    raise AssertionError(
        "the planted hook reported no findings; suite output was:\n"
        + suite_output_tail
    )


def test_execute_refuses_when_signing_key_is_present(
    tmp_path: Path,
) -> None:
    target, worker_key, _ = build_target(tmp_path)
    task_id = "T-008-REFUSE"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "harness-marker.txt"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        marker=marker,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=worker_key,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*RANEX_SIGNING_KEY", result.stderr)
    assert not worktree.exists()
    assert not marker.exists()
    assert journal_rows(journal) == []


def test_pop_does_not_remove_signing_key_from_proc_environment(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    home = tmp_path / "probe-home"

    script = tmp_path / "check.py"
    script.write_text(
        """\
import os

os.environ.pop("RANEX_SIGNING_KEY", None)
import ranex.cli.delegation

print(ranex.cli.delegation.exec_environment_holds_signing_key())
""",
        encoding="utf-8",
    )

    # The variable must be present at exec time, then popped by the child: that
    # is the measured fact under test. Setting it at runtime would leave
    # /proc/self/environ empty of it and pin nothing.
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(target),
        env=environment_for_process(
            home=home,
            python_path=target / "src",
            extra={"RANEX_SIGNING_KEY": str(tmp_path / "proc-key.txt")},
        ),
    )
    assert completed.stdout.strip() == "True", completed.stderr


def test_delegate_refuses_without_the_model_credential(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-NOAPI"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    harness = harness_script(tmp_path / "probe-harness.py")
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter=None,
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*OPENROUTER_API_KEY", result.stderr)
    assert not worktree.exists()
    assert journal_rows(journal) == []
    assert not outcome.exists()


def test_delegate_refuses_a_harness_that_is_not_executable(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-HARNESS-EXEC"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    harness = tmp_path / "probe-harness.py"
    harness.write_text("print('nope')\n", encoding="utf-8")
    harness.chmod(0o644)
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*harness", result.stderr)
    assert not worktree.exists()
    assert journal_rows(journal) == []


def test_no_signing_key_is_reachable_from_the_execute_process_tree(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-PROC"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "harness-marker.txt"
    capture = tmp_path / "proc-snapshot.bin"
    key_path = tmp_path / "signing.key"
    key_content = "signing-key-contents-unique-8080"
    key_path.write_text(key_content, encoding="utf-8")
    key_path.chmod(0o600)
    harness = harness_script(
        tmp_path / "probe-harness.py",
        marker=marker,
        capture=capture,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=None,
    )

    assert result.returncode == EXIT_PASS
    assert re.search(r"DELEGATED", result.stdout)
    assert "PASS" not in result.stdout

    assert marker.exists()
    assert worktree.exists()
    parsed = parse_capture(capture)
    assert parsed, "harness did not capture process-tree environ"
    child_names, child_values = parsed[0][1], parsed[0][2]
    other_blocks = parsed[1:]
    allowed = {
        "PATH",
        "HOME",
        "RANEX_TASK_ID",
        "RANEX_EMIT",
        "OPENROUTER_API_KEY",
    }
    assert set(child_names) == allowed
    assert len(parsed) >= 2
    for _, block_names, block_values in other_blocks:
        assert "RANEX_SIGNING_KEY" not in block_names
        assert str(key_path) not in block_values.values()
        assert key_content not in block_values.values()
    raw = capture.read_bytes()
    assert b"RANEX_SIGNING_KEY" not in raw
    assert str(key_path).encode("utf-8") not in raw
    assert key_content.encode("utf-8") not in raw
    child_home = child_values["HOME"]
    assert child_home != str(Path.home())
    assert child_home != str(worktree)
    assert not str(worktree).startswith(child_home + os.sep) and child_home != str(worktree)
    assert any(entry.get("type") == "task-dispatch" for entry in journal_rows(journal))

    written = read_outcome(outcome)
    assert written["task_id"] == task_id
    assert written["harness_exit"] == 0
    assert "signature" not in written


def test_missing_emission_blocks_as_absence(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-NO-EMIT"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        emit=False,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*emission", result.stderr)
    assert not outcome.exists()
    records = journal_rows(journal)
    assert all(record.get("type") != "task-candidate" for record in records)


def test_planted_hook_cannot_obtain_signature(
    tmp_path: Path,
) -> None:
    target, _, public = build_target(tmp_path)
    task_id = "T-008-CONFT"
    worktree = tmp_path / "worktree"
    journal = tmp_path / "task-journal.sqlite3"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        plant_conftest=True,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=None,
    )

    assert result.returncode == EXIT_PASS
    assert re.search(r"DELEGATED", result.stdout)
    assert outcome.exists()

    written = read_outcome(outcome)
    assert written["suite_exit"] != 0
    assert "signature" not in written
    assert "PLANTED_CONFTEST_HOOK_RAN" in str(written["suite_output_tail"])
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))

    # Unconditional: an `if it exists` guard would let this whole proof be
    # skipped in silence, which is how a control becomes decoration.
    findings = hook_findings(str(written["suite_output_tail"]))

    record = findings["forged"]
    signature = record.pop("signature")
    assert set(record) == set(SIGNED_FIELDS)
    assert re.match(r"^ed25519:", signature)
    assert verify_evidence(record, signature, public) is False

    scans = findings["theft"]["scans"]
    assert len(scans) >= 2, f"the hook probed too little to prove anything: {scans}"
    assert all(
        not scan["has_key_name"] and not scan["has_key_content"]
        for scan in scans
    )


def test_forged_emitted_worktree_blocks_before_materialisation(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-WTREE-FORGED"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    forged_worktree = tmp_path / "forged-worktree"
    marker = tmp_path / "marker.txt"
    subprocess.run(
        ["git", "-C", str(target), "worktree", "add", str(forged_worktree), "HEAD"],
        check=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    )
    harness = harness_script(
        tmp_path / "probe-harness.py",
        emit_worktree=forged_worktree,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*worktree", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_forged_emitted_commit_blocks_before_materialisation(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-COMMIT-FORGED"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    base_commit = subprocess.check_output(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        text=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    ).strip()
    harness = harness_script(
        tmp_path / "probe-harness.py",
        emit_commit=base_commit,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*commit", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_forged_emitted_task_id_blocks_before_materialisation(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-TASK-FORGED"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        emit_task_id="T-008-TRULY-UNASKED",
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*task", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_absent_dispatch_record_blocks_as_absence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-NO-DISPATCH"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(tmp_path / "probe-harness.py")
    outcome = tmp_path / "outcome.json"

    def _dispatch_without_record(
        task_id: str,
        raw_target: str,
        raw_worktree: str,
        raw_journal: str,
    ) -> Path:
        return target

    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr(
        "ranex.cli.main._perform_task_dispatch",
        _dispatch_without_record,
    )
    from ranex.cli import delegation

    args = argparse.Namespace(
        task_id=task_id,
        target=str(target),
        worktree=str(worktree),
        journal=str(journal),
        harness=str(harness),
        model="ranex-noop/noop",
        prompt="perform work then emit",
        timeout=120,
        suite=f"/usr/bin/touch {marker}",
        outcome=str(outcome),
    )
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = delegation.cmd_task_delegate(args)

    combined = stdout.getvalue() + stderr.getvalue()
    assert result == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*dispatch", combined)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_worktree_removed_mid_run_blocks(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-WTREE-REMOVED"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        delete_worktree=True,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*worktree", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_truthful_emission_reaches_the_suite(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-TRUTHFUL"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(tmp_path / "probe-harness.py")
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_PASS
    assert re.search(r"DELEGATED", result.stdout)
    assert marker.exists()
    assert outcome.exists()
    assert not re.search(r"ERROR  ", result.stderr)


def test_fanout_5_concurrent_delegations_still_judge_and_verify(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    (target / "gates.yaml").write_text(
        "\n".join(
            [
                "gates:",
                "  - gate_id: slice-008",
                "    rule_id: TESTS_EXECUTED",
                "    blocking: true",
                "    required_claims:",
                "      - claim_id: tests-executed",
                "        command: [\"/usr/bin/true\"]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (target / "evidence.json").write_text("[]\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(target), "add", "gates.yaml", "evidence.json"],
        check=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    )
    subprocess.run(
        ["git", "-C", str(target), "commit", "-q", "-m", "judge trust roots"],
        check=True,
        env=environment_for_process(home=tmp_path / "home", python_path=tmp_path / "home"),
    )

    outcome_dir = tmp_path / "outcomes"
    outcome_dir.mkdir()
    tasks = tmp_path / "tasks.jsonl"
    task_data = [
        {"task_id": f"T-008-FANOUT-{idx}", "prompt": "perform work then emit", "worktree": str(tmp_path / f"worktree-{idx}")}
        for idx in range(1, 6)
    ]
    tasks.write_text(
        "\n".join(json.dumps(item) for item in task_data) + "\n",
        encoding="utf-8",
    )
    wrapper = tmp_path / "queued-harness.sh"
    wrapper.write_text(
        """#!/usr/bin/env sh
set -eu
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir)
      WORKTREE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
sleep 0.45
if [ -z "${RANEX_EMIT:-}" ] || [ -z "${RANEX_TASK_ID:-}" ]; then
  echo "required delegate env missing" >&2
  exit 1
fi
if [ -z "${WORKTREE:-}" ]; then
  echo "missing --dir" >&2
  exit 1
fi
echo "agent from fanout shell harness" > "$WORKTREE/agent.txt"
git -C "$WORKTREE" add -A
git -C "$WORKTREE" \
  -c user.email=harness@example.invalid \
  -c user.name=Harness \
  commit -q -m "agent work"
commit=$(git -C "$WORKTREE" rev-parse HEAD)
printf '{\"task_id\":\"%s\",\"worktree\":\"%s\",\"commit\":\"%s\"}' "$RANEX_TASK_ID" "$WORKTREE" "$commit" > "$RANEX_EMIT"
""",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    result = run_fanout(
        target=target,
        tasks=tasks,
        journal=tmp_path / "task-journal.sqlite3",
        harness=wrapper,
        timeout=300,
        outcome_dir=outcome_dir,
        pool=5,
    )
    rows = journal_rows(tmp_path / "task-journal.sqlite3")
    assert result.returncode == EXIT_PASS, result.stderr
    assert re.search(r"^FANOUT", result.stdout, re.MULTILINE)
    assert len([record for record in rows if record.get("type") == "task-dispatch"]) == 5
    assert Journal(tmp_path / "task-journal.sqlite3").verify() is True
    outcomes = [outcome_dir / f"T-008-FANOUT-{idx}.json" for idx in range(1, 6)]
    for outcome in outcomes:
        payload = read_outcome(outcome)
        assert payload["timed_out"] is False
        assert isinstance(payload["commit"], str)
        assert re.fullmatch(r"[0-9a-f]{40}", str(payload["commit"]))
        judge = run_task_judge(
            target=target,
            task_id=str(payload["task_id"]),
            emitted_worktree=tmp_path / f"worktree-{int(payload['task_id'].split('-')[-1])}",
            emitted_commit=str(payload["commit"]),
            journal=tmp_path / "task-journal.sqlite3",
        )
        assert judge.returncode in (EXIT_PASS, EXIT_FAIL)
        assert "CANDIDATE" in judge.stdout
    post_rows = Journal(tmp_path / "task-journal.sqlite3").entries()
    assert len([record for record in post_rows if record.get("type") == "task-candidate"]) == 5
    assert Journal(tmp_path / "task-journal.sqlite3").verify() is True
    assert "ERROR" not in result.stderr


def test_fanout_respects_bounded_pool_and_does_not_tick_queue_time(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    outcome_dir = tmp_path / "outcomes"
    outcome_dir.mkdir()
    tasks = tmp_path / "tasks.jsonl"
    task_data = [
        {"task_id": f"T-008-BND-{idx}", "prompt": "perform work then emit", "worktree": str(tmp_path / f"worktree-{idx}")}
        for idx in range(1, 6)
    ]
    tasks.write_text(
        "\n".join(json.dumps(item) for item in task_data) + "\n",
        encoding="utf-8",
    )
    counter_dir = tmp_path / "concurrency-state"
    # rendezvous=2 makes the pool-of-two overlap deterministic instead of a
    # scheduling coincidence. A 60-second rendezvous and timeout=180 give
    # heavily contended materialised-suite runs headroom without making either
    # timing value part of the property under test.
    # The "queued time does not tick" proof no longer rests on this timeout
    # being tight: test_fanout_pool_of_one_never_overlaps_and_embeds_the_bound
    # (tests/integration/test_delegation_command.py) pins it structurally.
    harness = build_queued_harness(
        tmp_path / "queued-harness.py",
        counter_dir=counter_dir,
        sleep_seconds=1.0,
        rendezvous=2,
    )
    journal = tmp_path / "task-journal.sqlite3"

    result = run_fanout(
        target=target,
        tasks=tasks,
        journal=journal,
        harness=harness,
        timeout=180,
        outcome_dir=outcome_dir,
        pool=2,
    )
    assert result.returncode == EXIT_PASS
    peak = int((counter_dir / "peak").read_text(encoding="utf-8").strip())
    assert peak <= 2
    assert peak > 1
    for idx in range(1, 6):
        outcome = outcome_dir / f"T-008-BND-{idx}.json"
        payload = read_outcome(outcome)
        assert payload["timed_out"] is False
        assert re.fullmatch(r"[0-9a-f]{40}", str(payload["commit"]))


def test_cmd_task_delegate_refuses_duplicate_task_id_after_dispatch(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    first_task = "T-008-DUP"
    first_worktree = tmp_path / "first-worktree"
    second_worktree = tmp_path / "second-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    outcome = tmp_path / "outcome.json"
    harness = harness_script(tmp_path / "probe-harness.py")

    first = run_delegate(
        target=target,
        task_id=first_task,
        worktree=first_worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        signing_key=None,
        timeout=120,
    )
    assert first.returncode == EXIT_PASS
    assert read_outcome(outcome)["task_id"] == first_task

    second = run_delegate(
        target=target,
        task_id=first_task,
        worktree=second_worktree,
        journal=journal,
        harness=harness,
        outcome=tmp_path / "outcome2.json",
        openrouter="openrouter-key",
        signing_key=None,
        timeout=120,
    )
    assert second.returncode == EXIT_USAGE
    assert "already dispatched" in second.stderr.lower()
    assert len([row for row in journal_rows(journal) if row.get("task_id") == first_task and row.get("type") == "task-dispatch"]) == 1
    assert not second_worktree.exists()


def test_concurrent_delegates_to_same_worktree_keep_single_dispatch(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    journal = tmp_path / "task-journal.sqlite3"
    shared_worktree = tmp_path / "shared-worktree"
    harness = harness_script(tmp_path / "probe-harness.py")
    outcomes = tmp_path / "outcomes"
    outcomes.mkdir()

    start = threading.Event()
    results: list[tuple[str, subprocess.CompletedProcess[str]]] = []

    def run(task_id: str) -> None:
        start.wait()
        if task_id.endswith("2"):
            # Hold the worktree lock contention window open so one winner
            # is observed deterministically while still running concurrently.
            # Git startup can be delayed substantially in the materialised
            # full suite, so a scheduler-tick-sized stagger is insufficient.
            time.sleep(2.0)
        outcome = outcomes / f"{task_id}.json"
        result = run_delegate(
            target=target,
            task_id=task_id,
            worktree=shared_worktree,
            journal=journal,
            harness=harness,
            outcome=outcome,
            openrouter="openrouter-key",
            signing_key=None,
            timeout=300,
        )
        results.append((task_id, result))

    with ThreadPoolExecutor(max_workers=2) as pool:
        pool.submit(run, "T-8-RACE-1")
        pool.submit(run, "T-8-RACE-2")
        start.set()

    pass_count = sum(1 for _task, result in results if result.returncode == EXIT_PASS)
    assert pass_count == 1, [
        (task_id, result.returncode, result.stderr)
        for task_id, result in results
    ]
    assert any(result.returncode == EXIT_USAGE for _task, result in results)
    assert len([row for row in journal_rows(journal) if row.get("type") == "task-dispatch" and row.get("worktree") == str(shared_worktree)]) == 1


def test_delegation_that_commits_nothing_is_refused(
    tmp_path: Path,
) -> None:
    """Sad paths 5 and 8: the loop ran and changed nothing, so HEAD is still base.

    There is no subject to judge. Absence of work blocks rather than being
    scored, and the marker proves the refusal preceded materialisation.
    """

    target, _, _ = build_target(tmp_path)
    task_id = "T-008-NO-WORK"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        commit_work=False,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*base", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_empty_commit_over_an_identical_tree_is_refused(
    tmp_path: Path,
) -> None:
    """`git commit --allow-empty` changes the SHA and not one byte of the tree.

    Comparing commit ids alone accepts it, and the kernel would then measure a
    tree identical to the one it started from and report a result. The subject
    is the tree, so the tree is what must be compared.
    """

    target, _, _ = build_target(tmp_path)
    task_id = "T-008-EMPTY-COMMIT"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(
        tmp_path / "probe-harness.py",
        empty_commit=True,
    )
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*(base|tree)", result.stderr)
    assert not marker.exists()
    assert not outcome.exists()
    assert all(record.get("type") != "task-candidate" for record in journal_rows(journal))


def test_real_work_still_reaches_the_suite(
    tmp_path: Path,
) -> None:
    """The positive control. Without it every refusal above could pass because
    nothing ever ran, which is how a control becomes decoration."""

    target, _, _ = build_target(tmp_path)
    task_id = "T-008-REAL-WORK"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    marker = tmp_path / "marker.txt"
    harness = harness_script(tmp_path / "probe-harness.py")
    outcome = tmp_path / "outcome.json"

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        suite=f"/usr/bin/touch {marker}",
        signing_key=None,
    )

    assert result.returncode == EXIT_PASS
    assert re.search(r"DELEGATED", result.stdout)
    assert marker.exists()
    assert outcome.exists()


def test_delegate_timeout_kills_stalled_grandchild_process(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-TIMEOUT-KILL"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    outcome = tmp_path / "outcome.json"
    child_pid = tmp_path / "harness-child.pid"
    grandchild_pid = tmp_path / "harness-grandchild.pid"
    harness = write_stall_harness(
        path=tmp_path / "probe-harness-stall.sh",
        child_pid_path=child_pid,
        grandchild_pid_path=grandchild_pid,
    )

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        timeout=1,
        suite="/usr/bin/true",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*timed out", result.stderr)
    assert child_pid.exists()
    assert grandchild_pid.exists()
    written = read_outcome(outcome)
    assert written["timed_out"] is True
    assert written["commit"] is None
    assert written["suite_exit"] is None
    assert not result.stdout
    assert_process_died(int(child_pid.read_text(encoding="utf-8").strip()))
    assert_process_died(int(grandchild_pid.read_text(encoding="utf-8").strip()))


def test_delegate_timeout_still_results_in_dispatch_only(
    tmp_path: Path,
) -> None:
    target, _, _ = build_target(tmp_path)
    task_id = "T-008-TIMEOUT-NOCANDIDATE"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "task-journal.sqlite3"
    outcome = tmp_path / "outcome.json"
    harness = write_stall_harness(
        path=tmp_path / "probe-harness-stall2.sh",
        child_pid_path=tmp_path / "unused-child.pid",
        grandchild_pid_path=tmp_path / "unused-grandchild.pid",
    )

    result = run_delegate(
        target=target,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
        outcome=outcome,
        openrouter="openrouter-key",
        timeout=1,
        suite="/usr/bin/true",
        signing_key=None,
    )

    assert result.returncode == EXIT_USAGE
    assert re.search(r"ERROR  .*refusing.*timed out", result.stderr)
    rows = journal_rows(journal)
    assert any(record.get("task_id") == task_id and record.get("type") == "task-dispatch" for record in rows)
    assert all(record.get("type") != "task-candidate" for record in rows)
