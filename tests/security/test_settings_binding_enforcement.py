"""Real CLI admission binds committed policy, not the evidence's assertion."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from _approver import mint_approver, register_approver
from _history import mint_service, register_service

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import EXIT_FAIL, EXIT_USAGE, record_evidence, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.settings import load_settings, settings_digest, settings_schema_version
from ranex.foundation.signing import (
    ENVELOPE_TYPE,
    ENVELOPE_TYPE_V2,
    generate_keypair,
    sign_evidence,
)
from ranex.governed_execution.adapters.persistence.history import bootstrap_history
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

CATALOG = ('gates:\n  - gate_id: binding\n    rule_id: checked\n'
           '    requires_settings_binding: true\n    required_claims:\n'
           '      - claim_id: check\n        command: ["true"]\n')


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _binding_repo(tmp_path, *, catalog=CATALOG):
    """The temp-repo fixture: a governed application with a binding gate."""

    repo = tmp_path / 'application'
    repo.mkdir()
    _git(repo, 'init', '-q')
    _git(repo, 'config', 'user.name', 'Binding test')
    _git(repo, 'config', 'user.email', 'binding@example.invalid')
    (repo / 'governance').mkdir()
    worker_private, worker_public = generate_keypair()
    service_private, service_public, service_key = mint_service(tmp_path)
    key, approver_public = mint_approver(tmp_path)
    (repo / 'governance/gates.yaml').write_text(catalog)
    keyring = repo / 'governance/producers.yaml'
    keyring.write_text(
        f'producers:\n  worker: {worker_public}\n'
        f'verdict_signer:\n  id: kernel-verdict-signer\n  public_key: {service_public}\n'
    )
    register_service(keyring, service_public)
    register_approver(keyring, 'reviewer', approver_public)
    (repo / '.gitignore').write_text(
        'governance/evidence.json\ngovernance/observations.sqlite3*\n'
        'governance/journal.sqlite3*\n')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-qm', 'binding catalog')
    _git(repo, 'branch', '-M', 'main')
    return {
        'repo': repo,
        'catalog': catalog,
        'worker_private': worker_private,
        'service_private': service_private,
        'service_public': service_public,
        'service_key': service_key,
        'approver_key': key,
        'approver_private': key.read_text().strip(),
    }


def _cli_env(fixture, **extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RANEX_', 'GIT_', 'PYTHON'))}
    env.update(PYTHONPATH=str(Path(__file__).resolve().parents[2] / 'src'),
               RANEX_APPROVER_SIGNING_KEY=str(fixture['approver_key']),
               RANEX_VERDICT_SIGNING_KEY=str(fixture['service_key']))
    env.update(extra)
    return env


def _v1_record(fixture, repo, commit):
    """A correctly signed v1 record for the binding gate at ``commit``."""

    body = dict(claim_id='check', subject_digest=subject_digest_for(repo, commit),
                producer_id='worker', command='true', command_digest=command_digest(['true']),
                executable_path='/usr/bin/true', exit_code=0, suite_results=None,
                confinement_result_digest='sha256:' + 'c' * 64,
                confinement_profile_digest='sha256:' + 'd' * 64,
                envelope_type=ENVELOPE_TYPE, gate_id='binding',
                catalog_digest=catalog_digest_for(fixture['catalog'].encode()))
    return {**body, 'signature': sign_evidence(body, fixture['worker_private'])}


@pytest.mark.parametrize('version,expected', [(ENVELOPE_TYPE_V2, 0), (ENVELOPE_TYPE, 1)])
def test_cli_committed_binding_gate(tmp_path, version, expected):
    fixture = _binding_repo(tmp_path)
    repo = fixture['repo']
    commit = _git(repo, 'rev-parse', 'HEAD')
    body = dict(claim_id='check', subject_digest=subject_digest_for(repo, commit),
                producer_id='worker', command='true', command_digest=command_digest(['true']),
                executable_path='/usr/bin/true', exit_code=0, suite_results=None,
                confinement_result_digest='sha256:' + 'c' * 64,
                confinement_profile_digest='sha256:' + 'd' * 64,
                envelope_type=version, gate_id='binding',
                catalog_digest=catalog_digest_for(fixture['catalog'].encode()))
    if version == ENVELOPE_TYPE_V2:
        body.update(settings_digest=settings_digest(load_settings(repo, evaluated_ref=commit)),
                    settings_schema_version=settings_schema_version)
    evidence = repo / 'governance/evidence.json'
    checkpoint = tmp_path / 'checkpoint.json'
    bootstrap_history(evidence, checkpoint, fixture['service_private'],
                      fixture['service_public'], repo)
    record_evidence(evidence, {**body, 'signature': sign_evidence(body, fixture['worker_private'])},
                    repository_root=repo, history_public_key=fixture['service_public'],
                    history_private_key=fixture['service_private'],
                    history_checkpoint_path=checkpoint)
    env = _cli_env(fixture)
    argv = [sys.executable, '-m', 'ranex.cli.main', 'gate', 'evaluate', commit,
            '--external-repository', str(repo), '--gate', 'binding',
            '--approver', 'reviewer', '--history-checkpoint', str(checkpoint)]

    def evaluate():
        return subprocess.run(argv, cwd=repo, env=env, capture_output=True,
                               text=True, timeout=60, check=False)

    result = evaluate()
    assert result.returncode == expected, result.stdout + result.stderr
    assert ('PASS' if expected == 0 else 'FAIL') in result.stdout
    if expected:
        assert 'settings-binding-mismatch' in result.stdout
    assert (repo / 'governance/journal.sqlite3').exists()
    # A working-tree opt-out is not the catalog that the CLI judges: the
    # re-run refuses to produce any verdict from the divergent working-tree
    # copy — the committed flag is the only one that can decide (the first
    # run above already carries the settings-binding-mismatch verdict on
    # the v1 record). A regression to reading the working tree would
    # instead judge the rewritten `false` and PASS the v1 record.
    (repo / 'governance/gates.yaml').write_text(
        fixture['catalog'].replace('true\n    required', 'false\n    required'))
    again = evaluate()
    assert again.returncode == EXIT_USAGE, again.stdout + again.stderr
    assert 'differs from the version committed' in again.stdout + again.stderr


def test_cli_producer_envelope_follows_committed_catalog(tmp_path):
    """`run` emits v2 for a committed binding gate and v1 otherwise."""

    catalog = ('gates:\n  - gate_id: binding\n    rule_id: checked\n'
               '    requires_settings_binding: true\n    required_claims:\n'
               '      - claim_id: check\n        command: ["true"]\n'
               '  - gate_id: plain\n    rule_id: observed\n    required_claims:\n'
               '      - claim_id: observe\n        command: ["true"]\n')
    fixture = _binding_repo(tmp_path, catalog=catalog)
    repo = fixture['repo']
    worker_key = tmp_path / 'worker.key'
    worker_key.write_text(fixture['worker_private'] + '\n')
    worker_key.chmod(0o600)
    evidence = repo / 'governance/evidence.json'
    checkpoint = tmp_path / 'checkpoint.json'
    bootstrap_history(evidence, checkpoint, fixture['service_private'],
                      fixture['service_public'], repo)
    env = _cli_env(fixture, RANEX_SIGNING_KEY=str(worker_key))
    for gate, claim, envelope in (('binding', 'check', ENVELOPE_TYPE_V2),
                                  ('plain', 'observe', ENVELOPE_TYPE)):
        observed = subprocess.run(
            [sys.executable, '-m', 'ranex.cli.main', 'run',
             '--external-repository', str(repo), '--gate', gate, '--claim', claim,
             '--producer', 'worker', '--history-checkpoint', str(checkpoint),
             '--', 'true'],
            cwd=repo, env=env, capture_output=True, text=True, timeout=60, check=False)
        assert observed.returncode == 0, observed.stdout + observed.stderr
        assert json.loads(evidence.read_text())[-1]['envelope_type'] == envelope


def test_task_judge_and_merge_refuse_v1_evidence_at_binding_gate(tmp_path):
    """The task paths admit through the same committed binding policy."""

    fixture = _binding_repo(tmp_path)
    repo = fixture['repo']
    journal = repo / 'governance/journal.sqlite3'
    worktree = tmp_path / 'worktree-T-BIND'
    env = _cli_env(fixture)
    dispatched = subprocess.run(
        [sys.executable, '-m', 'ranex.cli.main', 'task', 'dispatch',
         '--task-id', 'T-BIND', '--target', str(repo),
         '--worktree', str(worktree), '--journal', str(journal)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert dispatched.returncode == 0, dispatched.stdout + dispatched.stderr
    (worktree / 'work.txt').write_text('the worker\'s real work\n')
    _git(worktree, 'add', '.')
    _git(worktree, 'commit', '-qm', 'the worker\'s real work')
    commit = _git(worktree, 'rev-parse', 'HEAD')
    evidence = worktree / 'governance/evidence.json'
    checkpoint = tmp_path / 'task-checkpoint.json'
    bootstrap_history(evidence, checkpoint, fixture['service_private'],
                      fixture['service_public'], worktree)
    record_evidence(evidence, _v1_record(fixture, worktree, commit),
                    repository_root=worktree,
                    history_public_key=fixture['service_public'],
                    history_private_key=fixture['service_private'],
                    history_checkpoint_path=checkpoint)

    judged = subprocess.run(
        [sys.executable, '-m', 'ranex.cli.main', 'task', 'judge',
         '--task-id', 'T-BIND', '--emitted-worktree', str(worktree),
         '--emitted-commit', commit, '--gate', 'binding',
         '--gate-catalog', 'governance/gates.yaml',
         '--evidence', 'governance/evidence.json',
         '--producers', 'governance/producers.yaml', '--journal', str(journal)],
        cwd=repo, env=_cli_env(fixture, RANEX_HISTORY_CHECKPOINT=str(checkpoint)),
        capture_output=True, text=True, timeout=60, check=False)
    # The v1 record is refused admission (settings-binding-mismatch), so the
    # candidate is materialised with the claim missing — never a default
    # PASS, and never the evaluator's "requires the CLI admission path" error
    # that a dropped binding tuple would raise.
    assert judged.returncode == EXIT_FAIL, judged.stdout + judged.stderr
    assert 'CANDIDATE' in judged.stdout
    assert 'ERROR' not in judged.stderr

    rows = [row for row in Journal(journal).entries()
            if row.get('type') == 'task-candidate' and row.get('task_id') == 'T-BIND']
    assert rows, 'the judge must record the candidate row'
    envelope = dict(candidate=commit, subject=subject_digest_for(repo, commit),
                    target_ref='refs/heads/main', tip=_git(repo, 'rev-parse', 'refs/heads/main'),
                    catalog_digest=catalog_digest_for(fixture['catalog'].encode()),
                    candidate_row_hash=candidate_row_hash(rows[-1]),
                    approver_id='worker')
    approval = tmp_path / 'approval.json'
    approval.write_text(json.dumps(
        {**envelope, 'signature': sign_approval(envelope, fixture['worker_private'])}))
    # `task merge` has no --external-repository: its governed root is the
    # checkout containing the CLI, so the merge arm drives the same CLI
    # entrypoint in-process with the root patched to the fixture target —
    # the frozen kernel-merge convention from tests/e2e/test_task_real.py.
    import contextlib
    import io

    import ranex.cli.main as cli_main
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(cli_main, 'governed_repository_root', lambda: repo.resolve())
        monkeypatch.setenv('RANEX_HISTORY_CHECKPOINT', str(checkpoint))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            merged = cli_main.main(
                ['task', 'merge', '--task-id', 'T-BIND', '--target-ref', 'refs/heads/main',
                 '--candidate', commit, '--approval', str(approval), '--journal', str(journal)])
    # The same refused record reaches the merge layer: no admitted evidence
    # can satisfy the binding gate, so publication is REFUSED — not the
    # evaluator error a dropped binding tuple would surface.
    assert merged == EXIT_FAIL, out.getvalue() + err.getvalue()
    assert 'REFUSED' in err.getvalue()
    assert 'sad-path-5 satisfying-evidence-missing' in err.getvalue()
