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
from ranex.cli.main import record_evidence, subject_digest_for
from ranex.foundation.canonical import command_digest
from ranex.foundation.settings import load_settings, settings_digest, settings_schema_version
from ranex.foundation.signing import (
    ENVELOPE_TYPE,
    ENVELOPE_TYPE_V2,
    generate_keypair,
    sign_evidence,
)
from ranex.governed_execution.adapters.persistence.history import bootstrap_history


@pytest.mark.parametrize('version,expected', [(ENVELOPE_TYPE_V2, 0), (ENVELOPE_TYPE, 1)])
def test_cli_committed_binding_gate(tmp_path, version, expected):
    repo = tmp_path / 'application'
    repo.mkdir()
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git('init', '-q')
    git('config', 'user.name', 'Binding test')
    git('config', 'user.email', 'binding@example.invalid')
    (repo / 'governance').mkdir()
    worker_private, worker_public = generate_keypair()
    service_private, service_public, service_key = mint_service(tmp_path)
    key, approver_public = mint_approver(tmp_path)
    catalog = ('gates:\n  - gate_id: binding\n    rule_id: checked\n'
               '    requires_settings_binding: true\n    required_claims:\n'
               '      - claim_id: check\n        command: ["true"]\n')
    (repo / 'governance/gates.yaml').write_text(catalog)
    keyring = repo / 'governance/producers.yaml'
    keyring.write_text(
        f'producers:\n  worker: {worker_public}\n'
        f'verdict_signer:\n  id: kernel-verdict-signer\n  public_key: {service_public}\n'
    )
    register_service(keyring, service_public)
    register_approver(keyring, 'reviewer', approver_public)
    (repo / '.gitignore').write_text('governance/evidence.json\ngovernance/observations.sqlite3*\ngovernance/journal.sqlite3*\n')
    git('add', '.')
    git('commit', '-qm', 'binding catalog')
    commit = git('rev-parse', 'HEAD')
    body = dict(claim_id='check', subject_digest=subject_digest_for(repo, commit),
                producer_id='worker', command='true', command_digest=command_digest(['true']),
                executable_path='/usr/bin/true', exit_code=0, suite_results=None,
                confinement_result_digest='sha256:' + 'c' * 64,
                confinement_profile_digest='sha256:' + 'd' * 64,
                envelope_type=version, gate_id='binding',
                catalog_digest=catalog_digest_for(catalog.encode()))
    if version == ENVELOPE_TYPE_V2:
        body.update(settings_digest=settings_digest(load_settings(repo, evaluated_ref=commit)),
                    settings_schema_version=settings_schema_version)
    evidence = repo / 'governance/evidence.json'
    checkpoint = tmp_path / 'checkpoint.json'
    bootstrap_history(evidence, checkpoint, service_private, service_public, repo)
    record_evidence(evidence, {**body, 'signature': sign_evidence(body, worker_private)},
                    repository_root=repo, history_public_key=service_public,
                    history_private_key=service_private, history_checkpoint_path=checkpoint)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RANEX_', 'GIT_', 'PYTHON'))}
    env.update(PYTHONPATH=str(Path(__file__).resolve().parents[2] / 'src'),
               RANEX_APPROVER_SIGNING_KEY=str(key),
               RANEX_VERDICT_SIGNING_KEY=str(service_key))
    result = subprocess.run([sys.executable, '-m', 'ranex.cli.main', 'gate', 'evaluate', commit,
                             '--external-repository', str(repo), '--gate', 'binding',
                             '--approver', 'reviewer', '--history-checkpoint', str(checkpoint)],
                            cwd=repo, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == expected, result.stdout + result.stderr
    assert ('PASS' if expected == 0 else 'FAIL') in result.stdout
    if expected:
        assert 'settings-binding-mismatch' in result.stdout
    assert (repo / 'governance/journal.sqlite3').exists()
    # A working-tree opt-out is not the catalog that the CLI judges.
    (repo / 'governance/gates.yaml').write_text(catalog.replace('true\n    required', 'false\n    required'))
    assert json.loads(evidence.read_text())[0]['envelope_type'] == version
