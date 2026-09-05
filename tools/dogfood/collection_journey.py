"""Observe actual six collection failure and recovery through the complete CLI.

Uses the existing external-repository onboarding, all real upstream test IDs,
and a broken import in the actual test module. Neither XML nor evidence is
fabricated. Run sequentially with other governed/confinement journeys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import coverage
import external_proof as proof

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    results = []
    with tempfile.TemporaryDirectory(prefix='ranex-six-collection-') as directory:
        scratch = Path(directory)
        proof.check_prerequisites(ROOT, 'HEAD')
        identity = proof.provision_kernel(scratch, ROOT, 'HEAD')
        repo, external = proof.clone_external(scratch, proof.EXTERNAL_URL, proof.EXTERNAL_REV)
        baseline = proof.measure_baseline(repo, scratch)
        setup = proof.onboard_governance(scratch / 'kernel', repo, scratch, 'HEAD', baseline['passing'], 0)
        shutil.copyfile(scratch / 'baseline.xml', out / 'baseline.xml')
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(scratch), 'LANG': 'C.UTF-8',
               'PYTHONPATH': str(repo / 'src'), 'RANEX_SIGNING_KEY': str(setup['key'])}
        measured = bool(os.environ.get('COVERAGE_PROCESS_START'))
        if measured:
            (out / 'coverage').mkdir()
            env.update(COVERAGE_PROCESS_START=str(ROOT / 'pyproject.toml'),
                       COVERAGE_FILE=str(out / 'coverage/.coverage'))
            env['PYTHONPATH'] += os.pathsep + str(ROOT / 'tests/e2e/coverage')

        def cli(*arguments):
            argv = [str(scratch / 'kernel/.venv/bin/python'), '-m', 'ranex.cli.main', *arguments]
            response = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True,
                                      check=False, timeout=900)
            commands.append(dict(argv=argv, exit=response.returncode, stdout=response.stdout, stderr=response.stderr))
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
            return response

        tests = repo / 'test_six.py'
        original = tests.read_bytes()
        manifest_ids = json.loads((repo / 'governance/suite_manifest.json').read_bytes())['suite']
        for phase in ('pristine', 'collection-failure', 'recovered'):
            if phase != 'pristine':
                tests.write_bytes(b"raise RuntimeError('collection journey: interrupted module import')\n" + original
                                  if phase == 'collection-failure' else original)
                for arguments in [('add', 'test_six.py'), ('commit', '-qm', phase)]:
                    commit = proof._git(repo, *arguments)
                    if commit.returncode:
                        raise RuntimeError(commit.stderr)
            collector_name = None
            if phase == 'collection-failure':
                # Retain the independent reporter's actual spelling. Pytest's
                # collection testcase can name a module rather than a path.
                artifact = out / 'independent-collection.xml'
                argv = [proof.PINNED_PY, '-m', 'pytest', '-q', f'--junitxml={artifact}',
                        *baseline['passing']]
                bare = subprocess.run(argv, cwd=repo, capture_output=True, text=True,
                                      timeout=300, check=False)
                commands.append(dict(argv=argv, exit=bare.returncode, stdout=bare.stdout, stderr=bare.stderr))
                collectors = [case.get('name') for case in ET.parse(artifact).iter('testcase')
                              if not case.get('classname') and case.find('error') is not None]
                if bare.returncode == 0 or len(collectors) != 1 or not collectors[0]:
                    raise RuntimeError('independent pytest did not report the broken collection')
                collector_name = collectors[0]
            observation = cli('run', '--producer', proof.PRODUCER, '--claim', 'tests-executed', '--', *setup['argv'])
            gate = cli('gate', 'evaluate', 'HEAD', '--approver', proof.APPROVER,
                       '--journal', 'governance/journal.sqlite3')
            evidence_path = repo / 'governance/evidence.json'
            evidence = json.loads(evidence_path.read_bytes())[0]
            shutil.copyfile(evidence_path, out / f'{phase}-evidence.json')
            summary = evidence['suite_results']
            ok = 'RECORDED' in observation.stdout
            if phase == 'collection-failure':
                ok = ok and observation.returncode != 0 and gate.returncode == 1
                ok = ok and summary['non_passed'] == [[collector_name, 'error']]
                ok = ok and summary['missing'] == manifest_ids
            else:
                ok = ok and observation.returncode == gate.returncode == 0
                ok = ok and summary['counts']['passed'] == setup['selected'] and not summary['missing']
            results.append(dict(phase=phase, verified=ok, suite_results=summary))
            (out / 'receipt.json').write_text(json.dumps(dict(kernel=identity, external=external,
                 baseline=baseline, results=results), indent=2) + '\n')
            print(phase, ok, flush=True)
            if not ok:
                raise RuntimeError(f'{phase} failed; see the actual commands and evidence')
        journal = cli('journal', 'verify', '--journal', 'governance/journal.sqlite3')
        if journal.returncode:
            raise RuntimeError(journal.stdout + journal.stderr)
        shutil.copyfile(repo / 'governance/journal.sqlite3', out / 'journal.sqlite3')
        if measured:
            # Use coverage.py's own path mapping only after proving this
            # vendored tree is byte-identical. Historical or modified kernels
            # must never be mapped onto this checkout's line numbers.
            expected = {str(p.relative_to(ROOT / 'src/ranex')): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (ROOT / 'src/ranex').rglob('*.py')}
            actual = {str(p.relative_to(repo / 'src/ranex')): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (repo / 'src/ranex').rglob('*.py')}
            if actual != expected:
                raise RuntimeError('refusing coverage mapping from a different kernel source')
            destination = Path(os.environ['COVERAGE_FILE']).absolute()
            mapped = destination.with_name(destination.name + f'.six-collection-{os.getpid()}')
            cov = coverage.Coverage(config_file=str(ROOT / 'pyproject.toml'), data_file=str(mapped))
            cov.set_option('paths', {'ranex': [str(ROOT / 'src/ranex'), str(repo / 'src/ranex')]})
            cov.combine(data_paths=[str(out / 'coverage')], strict=True, keep=True)
            cov.save()
            (out / 'coverage-mapping.json').write_text(json.dumps(dict(source_files=expected,
                observed_root=str(repo / 'src/ranex'), mapped_root=str(ROOT / 'src/ranex'),
                output=str(mapped)), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
