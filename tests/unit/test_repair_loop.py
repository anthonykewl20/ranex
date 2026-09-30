"""Repair hook control wiring, independent of execution qualification."""
import argparse
import json
from types import SimpleNamespace

import pytest

from ranex.cli import main as cli
from ranex.cli import repair_loop
from ranex.foundation.signing import generate_keypair
from ranex.governed_execution import verdict_reader


@pytest.fixture
def loop(monkeypatch, tmp_path):
    worker_private, worker_public = generate_keypair()
    _, service_public = generate_keypair()
    catalog = b"gates:\n  - gate_id: release\n    rule_id: TESTS\n    blocking: true\n    required_claims:\n      - claim_id: tests\n        command: [pytest, tests, -q]\n"
    trust = (f"producers:\n  worker: {worker_public}\nverdict_signer:\n  id: kernel-verdict-signer\n  public_key: {service_public}\n").encode()
    monkeypatch.setattr(cli, "_command_repository", lambda _: tmp_path)
    monkeypatch.setattr(cli, "head_commit", lambda _: "a" * 40)
    monkeypatch.setattr(cli, "subject_digest_for", lambda *_: "sha256:" + "b" * 64)
    monkeypatch.setattr(cli, "committed_trust_root", lambda _root, _commit, name, *_: trust if name == "producers.yaml" else catalog)
    monkeypatch.setenv("RANEX_SIGNING_KEY", worker_private)
    monkeypatch.setattr(repair_loop, "_read_hook_stdin", lambda: {"session_id": "same-task"})
    monkeypatch.setattr(verdict_reader, "read_verdict", lambda *_args, **_kwargs: SimpleNamespace(state=verdict_reader.ReadState.VERIFIED, record={"verdict": "FAIL"}))
    calls = []
    monkeypatch.setattr(repair_loop, "_run_cli", lambda argv: (calls.append(argv) or 0, "RECORDED"))
    args = argparse.Namespace(mode="stop", budget=3, gate="release", claim="tests", producer="worker", approver="owner", gate_catalog="gates.yaml", suite_manifest="suite.json", evidence="evidence.json", producers="producers.yaml", journal="journal.sqlite3", verdicts_dir="verdicts", external_repository=str(tmp_path), loop_id=None)
    return args, calls

def test_hook_forwards_selected_gate_to_evaluation(loop, capsys):
    args, calls = loop
    assert repair_loop.cmd_task_stop_hook(args) == 0
    evaluation = next(argv for argv in calls if argv[:2] == ["gate", "evaluate"])
    assert evaluation[evaluation.index("--gate") + 1] == "release"
    assert json.loads(capsys.readouterr().out)["misses"] == 1

def test_hook_budget_survives_subject_changes(loop, monkeypatch, capsys):
    args, _ = loop
    for count in range(1, 4):
        monkeypatch.setattr(cli, "subject_digest_for", lambda *_, count=count: "sha256:" + str(count) * 64)
        assert repair_loop.cmd_task_stop_hook(args) == 0
        response = json.loads(capsys.readouterr().out)
        assert response["misses"] == count
    assert response["decision"] == "approve"
    assert "budget exhausted" in response["reason"]

@pytest.mark.parametrize("command", ["pytest tests -q", "cd app && pytest tests -q", "MODE=1 pytest tests -q", "env MODE=1 pytest tests -q", "command pytest tests -q", "echo first; pytest tests -q"])
def test_pretool_blocks_wrapped_governed_suite(loop, monkeypatch, capsys, command):
    args, _ = loop
    args.mode = "pretooluse"
    monkeypatch.setattr(repair_loop, "_read_hook_stdin", lambda: {"tool_input": {"command": command}})
    assert repair_loop.cmd_task_stop_hook(args) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "block"

def test_pretool_allows_unrelated_simple_command(loop, monkeypatch, capsys):
    args, _ = loop
    args.mode = "pretooluse"
    monkeypatch.setattr(repair_loop, "_read_hook_stdin", lambda: {"tool_input": {"command": "git status --short"}})
    assert repair_loop.cmd_task_stop_hook(args) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"

@pytest.mark.parametrize("command", [
    "command env MODE=1 pytest tests -q",
    "env -S 'pytest tests -q'",
    "env --split-string='pytest tests -q'",
    "exec env --ignore-environment pytest tests -q",
    "sh -c 'pytest tests -q'",
])
def test_pretool_blocks_nested_command_wrappers(loop, monkeypatch, capsys, command):
    args, _ = loop
    args.mode = "pretooluse"
    monkeypatch.setattr(repair_loop, "_read_hook_stdin", lambda: {"tool_input": {"command": command}})
    assert repair_loop.cmd_task_stop_hook(args) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_simultaneous_verified_failures_all_spend_their_miss(
    loop, monkeypatch, tmp_path,
):
    import contextlib
    import io
    import multiprocessing
    import time

    args, _ = loop
    args.budget = 20
    original = repair_loop._read_misses

    def slow_read(path):
        value = original(path)
        time.sleep(0.1)
        return value

    monkeypatch.setattr(repair_loop, '_read_misses', slow_read)
    ctx = multiprocessing.get_context('fork')
    start = ctx.Barrier(4)
    output = ctx.Queue()

    def invoke():
        captured = io.StringIO()
        start.wait(timeout=5)
        with contextlib.redirect_stdout(captured):
            code = repair_loop.cmd_task_stop_hook(args)
        output.put((code, captured.getvalue()))

    children = [ctx.Process(target=invoke) for _ in range(4)]
    try:
        for child in children:
            child.start()
        results = [output.get(timeout=10) for _ in children]
        for child in children:
            child.join(timeout=5)
            assert child.exitcode == 0
        assert all(code == 0 for code, _ in results), results
        assert sorted(json.loads(raw)['misses'] for _, raw in results) == [1, 2, 3, 4]
        counter = next((tmp_path / 'verdicts').glob('*.budget.json'))
        assert original(counter) == 4
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
        output.close()
        output.join_thread()


@pytest.mark.parametrize('content', ['broken', '{"misses":true}', '{"misses":-1}',
                                      '{"misses":"2"}', '{"other":1}'])
def test_invalid_budget_state_is_refused_without_reset(loop, tmp_path, capsys, content):
    args, _ = loop
    assert repair_loop.cmd_task_stop_hook(args) == 0
    capsys.readouterr()
    counter = next((tmp_path / 'verdicts').glob('*.budget.json'))
    counter.chmod(0o600)
    counter.write_text(content)
    assert repair_loop.cmd_task_stop_hook(args) == 2
    assert 'budget' in capsys.readouterr().err
    assert counter.read_text() == content


def test_verified_pass_resets_counter_without_deleting_state(
    loop, monkeypatch, tmp_path, capsys,
):
    args, _ = loop
    assert repair_loop.cmd_task_stop_hook(args) == 0
    capsys.readouterr()
    counter = next((tmp_path / 'verdicts').glob('*.budget.json'))
    monkeypatch.setattr(verdict_reader, 'read_verdict', lambda *_args, **_kwargs:
        SimpleNamespace(state=verdict_reader.ReadState.VERIFIED, record={'verdict': 'PASS'}))
    assert repair_loop.cmd_task_stop_hook(args) == 0
    assert json.loads(capsys.readouterr().out)['misses'] == 0
    assert counter.is_file()
    assert repair_loop._read_misses(counter) == 0
