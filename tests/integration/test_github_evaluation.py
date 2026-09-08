"""Real observation and kernel subprocesses; only GitHub's API is local."""
from __future__ import annotations

import json
import socket
import subprocess
import threading
from dataclasses import replace
from types import SimpleNamespace

import _github_fake
import pytest
import test_external_repository
import yaml
from test_external_repository import commit, git, invoke

from ranex.bootstrap.composition import catalog_digest_for
from ranex.github_app.acceptance import resolve_acceptance
from ranex.github_app.binding import bind_pr_head
from ranex.github_app.evaluation import EvidenceEvaluator
from ranex.github_app.receiver import _ReceiverState, process_delivery, refresh_awaiting

application = test_external_repository.application


def test_fresh_evidence_is_judged_without_executing_pr_code(application, monkeypatch):
    repo, worker, signer, public = application
    ignore = repo / '.gitignore'
    ignore.write_text(ignore.read_text() + '.local/\n')
    commit(repo)
    command = yaml.safe_load(
        (repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    frozen = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert frozen.returncode == 0, frozen.stderr
    commit(repo)
    evaluator = EvidenceEvaluator(repo, 'governance/evidence.json', 'landing',
                                  'governance/gates.yaml', 'governance/producers.yaml',
                                  'governance/suite_manifest.json', 'pilot',
                                  repo / 'governance/verdicts', signer, repo / '.local/evaluation')

    def acceptance():
        binding = bind_pr_head(repo, git(repo, 'rev-parse', 'HEAD'))
        evaluator(binding)
        return resolve_acceptance(evaluator.verdicts_dir, binding,
                                  {'kernel-verdict-signer': public}, gate_id='landing',
                                  catalog_digest=catalog_digest_for(
                                      (repo / 'governance/gates.yaml').read_bytes()), approver_id='pilot')

    assert not acceptance().publishable
    observed = invoke(repo, 'run', '--external-repository', str(repo), '--claim', 'tests-executed',
                      '--producer', 'worker', '--', *command, key=worker)
    assert observed.returncode == 0, observed.stderr
    assert acceptance().record['verdict'] == 'PASS'
    evidence_path = repo / 'governance/evidence.json'
    valid_evidence = evidence_path.read_bytes()
    evidence_path.write_bytes(b'{')
    with pytest.raises(ValueError, match='EVALUATION-REFUSED'):
        acceptance()
    evidence_path.write_bytes(valid_evidence + b'\n')
    timeout_binding = bind_pr_head(repo, git(repo, 'rev-parse', 'HEAD'))
    actual_run = subprocess.run
    with monkeypatch.context() as patcher:
        def timeout(*args, **kwargs):
            if 'ranex.cli.main' in args[0]:
                raise subprocess.TimeoutExpired(args[0], 60)
            return actual_run(*args, **kwargs)
        patcher.setattr(subprocess, 'run', timeout)
        with pytest.raises(ValueError, match='EVALUATION-TIMEOUT'):
            evaluator(timeout_binding)
    with monkeypatch.context() as patcher:
        def move_evidence(*args, **kwargs):
            result = actual_run(*args, **kwargs)
            if 'ranex.cli.main' in args[0]:
                evidence_path.write_bytes(evidence_path.read_bytes() + b'\n')
            return result
        patcher.setattr(subprocess, 'run', move_evidence)
        with pytest.raises(ValueError, match='EVIDENCE-MOVED'):
            evaluator(timeout_binding)
    assert acceptance().record['verdict'] == 'PASS'
    publications = list(evaluator.verdicts_dir.glob('*.json'))
    original = publications[0].read_bytes()
    assert acceptance().record['verdict'] == 'PASS'
    assert publications[0].read_bytes() == original  # no repeated judgment/journal append
    (repo / 'src/application.py').write_text('VALUE = 41\n')
    commit(repo)
    assert acceptance().record['verdict'] == 'FAIL'  # stale evidence is not authority
    observed = invoke(repo, 'run', '--external-repository', str(repo), '--claim', 'tests-executed',
                      '--producer', 'worker', '--', *command, key=worker)
    assert observed.returncode == 1
    assert acceptance().record['verdict'] == 'FAIL'
    (repo / 'src/application.py').write_text('VALUE = 42  # repaired\n')
    commit(repo)
    assert acceptance().record['verdict'] == 'FAIL'
    observed = invoke(repo, 'run', '--external-repository', str(repo), '--claim', 'tests-executed',
                      '--producer', 'worker', '--', *command, key=worker)
    assert observed.returncode == 0, observed.stderr
    assert acceptance().record['verdict'] == 'PASS'
    # A webhook head cannot replace the operator's reviewed test manifest.
    trusted = (repo / 'governance/suite_manifest.json').read_bytes()
    (repo / 'governance/suite_manifest.json').write_text('{}\n')
    commit(repo)
    changed = bind_pr_head(repo, git(repo, 'rev-parse', 'HEAD'))
    (repo / 'governance/suite_manifest.json').write_bytes(trusted)
    with pytest.raises(ValueError, match='committed|differ|dirty|match'):
        evaluator(changed)
    (repo / 'governance/suite_manifest.json').write_text('{}\n')
    with pytest.raises(ValueError, match='POLICY-CHANGED'):
        evaluator(changed)  # even changing the operator checkout cannot repin a running process


def test_receiver_rejudges_late_evidence_and_recovers_without_duplicate_success(application, tmp_path):
    repo, worker, signer, public = application
    ignore = repo / '.gitignore'
    ignore.write_text(ignore.read_text() + '.local/\n')
    commit(repo)
    command = yaml.safe_load((repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    result = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert result.returncode == 0, result.stderr
    commit(repo)
    evaluator = EvidenceEvaluator(repo, 'governance/evidence.json', 'landing',
                                  'governance/gates.yaml', 'governance/producers.yaml',
                                  'governance/suite_manifest.json', 'pilot',
                                  repo / 'governance/verdicts', signer, repo / '.local/evaluation')
    with _github_fake.receiver_environment(tmp_path / 'api', with_verdict=False) as env:
        config = replace(env.config, repo_root=repo, remote=str(repo), evaluator=evaluator,
                         verdicts_dir=evaluator.verdicts_dir, approver_id='pilot',
                         keyring={'kernel-verdict-signer': public},
                         catalog_digest=catalog_digest_for((repo / 'governance/gates.yaml').read_bytes()))
        head = git(repo, 'rev-parse', 'HEAD')
        body = _github_fake.pull_request_event_body(head)
        assert process_delivery(config, env.state, body, 'automatic', 'pull_request') == 200
        assert env.fake.check_requests[-1]['body']['conclusion'] == 'action_required'
        assert refresh_awaiting(config, env.state) == {}
        assert len(env.fake.check_requests) == 1
        # Nonempty but missing evidence produces FAIL, never success from exit zero alone.
        (repo / 'governance/evidence.json').write_text('[]\n')
        assert refresh_awaiting(config, env.state) == {head: 'failure'}
        count = len(env.fake.check_requests)
        assert refresh_awaiting(config, _ReceiverState()) == {}
        assert len(env.fake.check_requests) == count
        completion = next((config.state_dir / 'evaluations').glob('*.json'))
        receipt = completion.read_bytes()
        completion.chmod(0o600)
        completion.write_text('[]\n')
        assert refresh_awaiting(config, _ReceiverState()) == {head: 500}
        completion.write_bytes(receipt)
        (config.state_dir / 'awaiting' / f'{head}.failed').unlink()

        result = invoke(repo, 'run', '--external-repository', str(repo), '--claim', 'tests-executed',
                        '--producer', 'worker', '--', *command, key=worker)
        assert result.returncode == 0, result.stderr
        waiting = config.state_dir / 'awaiting' / f'{head}.json'
        retained = waiting.read_bytes()
        env.fake.fail_check_runs_with = 503
        assert refresh_awaiting(config, env.state) == {head: 500}
        env.fake.fail_check_runs_with = None
        waiting.with_suffix('.failed').unlink()
        assert refresh_awaiting(config, _ReceiverState()) == {head: 'success'}
        count = len(env.fake.check_requests)
        # Simulate a crash after GitHub accepted the check, before local completion.
        waiting.write_bytes(retained)
        assert refresh_awaiting(config, _ReceiverState()) == {}
        assert not waiting.exists()
        assert len(env.fake.check_requests) == count
        for path in (config.state_dir / 'evaluations').glob('*.json'):
            if json.loads(path.read_bytes())['conclusion'] == 'success':
                path.unlink()
        waiting.write_bytes(retained)
        assert refresh_awaiting(config, _ReceiverState()) == {}
        assert not waiting.exists()
        assert len(env.fake.check_requests) == count



def test_listener_requires_a_matching_external_signer_before_enabling_evaluation(application, tmp_path, monkeypatch):
    from ranex.cli.main import main
    from ranex.github_app import receiver

    repo, worker, signer, _public = application
    command = yaml.safe_load((repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    result = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert result.returncode == 0, result.stderr
    commit(repo)
    key, _ = _github_fake.write_app_key(tmp_path / 'app-key')
    monkeypatch.setenv('RANEX_GITHUB_APP_ID', _github_fake.APP_ID)
    monkeypatch.setenv('RANEX_GITHUB_APP_PRIVATE_KEY', str(key))
    monkeypatch.setenv('RANEX_GITHUB_WEBHOOK_SECRET', _github_fake.WEBHOOK_SECRET)
    monkeypatch.delenv('RANEX_VERDICT_SIGNING_KEY', raising=False)
    argv = ['github', 'listen', '--repository', str(repo), '--repo', 'owner/name',
            '--installation', '1', '--approver', 'pilot', '--evaluate-evidence']
    configurations = []
    real_serve = receiver.serve
    def capture(config, bind, **kwargs):
        configurations.append(config)
        kwargs['on_listen'](SimpleNamespace(server_port=bind[1]))
    monkeypatch.setattr(receiver, 'serve', capture)
    assert main(argv) == 2
    monkeypatch.setenv('RANEX_VERDICT_SIGNING_KEY', str(worker))
    assert main(argv) == 2
    assert configurations == []
    monkeypatch.setenv('RANEX_VERDICT_SIGNING_KEY', str(signer))
    assert main(argv) == 0
    assert isinstance(configurations[0].evaluator, EvidenceEvaluator)

    assert main(['github', 'register', '--repository', str(repo),
                 '--credentials-dir', str(tmp_path / 'registration'),
                 '--homepage', 'https://example.com', '--webhook-url', 'https://example.com/hook',
                 '--bind', '127.0.0.1:65536']) == 2
    assert main(argv + ['--bind', '127.0.0.1:65536']) == 2
    assert len(configurations) == 1
    monkeypatch.setattr(receiver, 'serve', real_serve)
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1', 0))
        occupied.listen()
        threads = set(threading.enumerate())
        assert main(argv + ['--bind', f'127.0.0.1:{occupied.getsockname()[1]}']) == 2
        assert set(threading.enumerate()) == threads

    # If the startup callback refuses, close the socket without starting work.
    addresses = []
    def refuse(server):
        addresses.append(server.server_address)
        raise ValueError('startup refused')
    with pytest.raises(ValueError, match='startup refused'):
        real_serve(configurations[0], ('127.0.0.1', 0), on_listen=refuse)
    with socket.socket() as reusable:
        reusable.bind(addresses[0])
    assert set(threading.enumerate()) == threads
