"""User-level evidence journeys retain marker-level XPASS and refuse missing reporting."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest
import test_external_repository
import yaml
from test_external_repository import commit, git, invoke

from ranex.cli.delegation import _run_suite_with_results
from ranex.cli.suite_observer import PLUGIN, pytest_observer_environment
from ranex.foundation.suite_results import freeze_manifest, suite_results_from_junitxml

application = test_external_repository.application


def test_explicit_xpass_blocks_signed_acceptance_and_recovers(application):
    repo, worker, signer, _public = application
    command = yaml.safe_load((repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    frozen = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    commit(repo)
    source = (repo / 'test_application.py').read_text()
    (repo / 'test_application.py').write_text(
        'import pytest\n' + source.replace('def test_value():',
        '@pytest.mark.xfail(strict=False, reason="known issue")\ndef test_value():'))
    commit(repo)
    observed = invoke(repo, 'run', '--external-repository', str(repo), '--producer', 'worker',
                      '--claim', 'tests-executed', '--', *command, key=worker)
    assert observed.returncode == 1, observed.stdout + observed.stderr
    records = json.loads((repo / 'governance/evidence.json').read_bytes())
    assert records[-1]['suite_results']['counts']['xpassed'] == 1
    judged = invoke(repo, 'gate', 'evaluate', 'HEAD', '--external-repository', str(repo),
                    '--approver', 'pilot', verdict_key=signer)
    assert judged.returncode == 1 and '(xpassed)' in judged.stdout, judged.stdout + judged.stderr
    (repo / 'test_application.py').write_text(source)
    commit(repo)
    assert invoke(repo, 'run', '--external-repository', str(repo), '--producer', 'worker',
                  '--claim', 'tests-executed', '--', *command, key=worker).returncode == 0
    assert invoke(repo, 'gate', 'evaluate', 'HEAD', '--external-repository', str(repo),
                  '--approver', 'pilot', verdict_key=signer).returncode == 0
    # An ordinary pytest configuration can disable an environment-loaded plugin.
    # A passing exit without the marker must not replace the signed evidence.
    evidence = (repo / 'governance/evidence.json').read_bytes()
    (repo / 'pytest.ini').write_text(f'[pytest]\naddopts = -p no:{PLUGIN}\n')
    commit(repo)
    refused = invoke(repo, 'run', '--external-repository', str(repo), '--producer', 'worker',
                     '--claim', 'tests-executed', '--', *command, key=worker)
    assert refused.returncode == 2 and 'E-PYTEST-OBSERVER-ABSENT' in refused.stderr
    assert (repo / 'governance/evidence.json').read_bytes() == evidence
    frozen = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert frozen.returncode == 2 and 'E-PYTEST-OBSERVER-ABSENT' in frozen.stderr
    for addopts in ('--runxfail', '-p no:skipping'):
        (repo / 'pytest.ini').write_text(f'[pytest]\naddopts = {addopts}\n')
        commit(repo)
        refused = invoke(repo, 'run', '--external-repository', str(repo), '--producer', 'worker',
                         '--claim', 'tests-executed', '--', *command, key=worker)
        assert refused.returncode == 2
        assert 'E-PYTEST-XFAIL-DISABLED' in refused.stdout + refused.stderr
        assert (repo / 'governance/evidence.json').read_bytes() == evidence


def test_real_pytest_outcome_matrix_preserves_all_outcomes(tmp_path):
    (tmp_path / 'test_matrix.py').write_text('''import pytest
def test_pass(): pass
def test_fail(): assert False
@pytest.mark.skip(reason="platform")
def test_skip(): pass
@pytest.mark.xfail(strict=False, reason="known")
def test_xfail(): assert False
@pytest.mark.xfail(strict=False, reason="unexpected")
def test_xpass(): pass
@pytest.mark.xfail(strict=True, reason="unexpected")
def test_strict_xpass(): pass
''')
    environment = {**os.environ, **pytest_observer_environment(tmp_path)}
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-o', 'xfail_strict=true',
                             '--junitxml=result.xml'], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 1, result.stdout + result.stderr
    raw = (tmp_path / 'result.xml').read_bytes()
    manifest = freeze_manifest(raw, require_pytest_observer=True)
    summary = suite_results_from_junitxml(raw, manifest, require_pytest_observer=True)
    assert summary['counts'] == dict(passed=1, failed=1, errors=0, skipped=1, xfailed=1, xpassed=2)
    for changed in (
        raw.replace(b'name="ranex.pytest_observer"', b'name="absent"'),
        raw.replace(b'value="1"', b'value="unsupported"'),
        raw.replace(b'</properties>', b'<property name="ranex.pytest_observer" value="1" /></properties>'),
    ):
        with pytest.raises(ValueError, match='E-PYTEST-OBSERVER-ABSENT'):
            suite_results_from_junitxml(changed, manifest, require_pytest_observer=True)


def test_delegation_reports_explicit_xpass_before_materialisation_cleanup(application):
    repo, _worker, _signer, _public = application
    command = yaml.safe_load((repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    frozen = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command)
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    source = (repo / 'test_application.py').read_text()
    (repo / 'test_application.py').write_text('import pytest\n' + source.replace(
        'def test_value():', '@pytest.mark.xfail(strict=False)\ndef test_value():'))
    commit(repo)
    import shlex
    code, _tail, summary = _run_suite_with_results(
        repo, git(repo, 'rev-parse', 'HEAD'), shlex.join(command),
        results_artifact='governance/suite_results.xml',
        manifest=json.loads((repo / 'governance/suite_manifest.json').read_bytes()),
    )
    assert code == 1 and summary['counts']['xpassed'] == 1
