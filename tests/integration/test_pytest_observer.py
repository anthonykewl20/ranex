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
from ranex.cli.suite_observer import PLUGIN
from ranex.foundation.suite_results import freeze_manifest, suite_results_from_junitxml

application = test_external_repository.application


def test_explicit_xpass_blocks_signed_acceptance_and_recovers(application):
    repo, worker, signer, _public = application
    command = yaml.safe_load((repo / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
    frozen = invoke(repo, 'suite', 'freeze', '--external-repository', str(repo),
                    '--artifact', 'governance/suite_results.xml', '--', *command,
                    '-p', 'ranex.foundation.pytest_xpass')
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
    confined = invoke(repo, 'run', '--external-repository', str(repo), '--producer', 'worker',
                      '--claim', 'tests-executed', '--confinement', 'strict-local', '--', *command,
                      key=worker)
    assert confined.returncode == 2 and 'E-PYTEST-OBSERVER-CONFINEMENT' in confined.stderr
    assert (repo / 'governance/evidence.json').read_bytes() == evidence
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
        # The supervised child's diagnostic is streamed independently; the
        # controller must refuse the absent artifact in every capture mode.
        assert 'results artifact is absent' in refused.stderr
        assert (repo / 'governance/evidence.json').read_bytes() == evidence


def test_real_pytest_outcome_matrix_preserves_all_outcomes(tmp_path):
    (tmp_path / 'test_matrix.py').write_text('''import pytest
def test_pass():
    import os, subprocess, sys
    from pathlib import Path
    child = Path("child")
    child.mkdir()
    (child / "test_child.py").write_text("import pytest\\n@pytest.mark.xfail(strict=False)\\ndef test_child(): pass\\n")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=child,
                            env={**os.environ, "PYTHONPATH": str(child.resolve())},
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

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
    kernel = test_external_repository.KERNEL
    environment = {**os.environ, "PYTHONPATH": str(kernel / "src"),
                   "PYTEST_PLUGINS": "ranex.foundation.pytest_xpass"}
    prefix = [sys.executable]
    if environment.get("COVERAGE_PROCESS_START") or environment.get("COVERAGE_PROCESS_CONFIG"):
        environment.pop("COVERAGE_PROCESS_START", None)
        environment.pop("COVERAGE_PROCESS_CONFIG", None)
        prefix += ["-m", "coverage", "run", f"--rcfile={kernel / 'pyproject.toml'}",
                   f"--source={kernel / 'src/ranex'}"]
    result = subprocess.run([*prefix, '-m', 'pytest', '-q', '-o', 'xfail_strict=true',
                             '--junitxml=result.xml'], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 1, result.stdout + result.stderr
    for disabled in (["--runxfail"], ["-p", "no:skipping"]):
        refused = subprocess.run([*prefix, "-m", "pytest", *disabled], cwd=tmp_path,
                                 env=environment, capture_output=True, text=True, check=False)
        assert refused.returncode == 4 and "E-PYTEST-XFAIL-DISABLED" in refused.stderr
    (tmp_path / 'other_plugin.py').write_text(
        'import os\nfrom pathlib import Path\n'
        'def pytest_sessionfinish(session):\n'
        '    Path("activation.txt").write_text(os.environ.get("PYTEST_PLUGINS", ""))\n')
    other = subprocess.run([*prefix, '-m', 'pytest', '-q', '-k', 'test_strict_xpass'],
                           cwd=tmp_path, capture_output=True, text=True, check=False,
                           env={**environment, 'PYTHONPATH': str(kernel / 'src') + os.pathsep + str(tmp_path),
                                'PYTEST_PLUGINS': 'ranex.foundation.pytest_xpass,other_plugin'})
    assert other.returncode == 1, other.stdout + other.stderr
    assert (tmp_path / 'activation.txt').read_text() == 'other_plugin'
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
