"""Build real Ranex candidate packages and check their installed version protocol.

Uses a fresh clone of the actual checkout, its locked dependencies, real wheel
and sdist builds, and installed CLI processes. Invalid release candidates must
remain identifiable while the release command refuses their tag spelling.
No tag, push, GitHub credential, or fabricated package is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import tomllib
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands: list[dict] = []
    results: list[dict] = []

    def run(argv, cwd, env=None):
        result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                                text=True, capture_output=True, check=False, timeout=300)
        commands.append(dict(argv=[str(x) for x in argv], cwd=str(cwd), exit=result.returncode,
                             stdout=result.stdout, stderr=result.stderr))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return result

    def require(result):
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout.strip()

    kernel = require(run(['git', 'rev-parse', 'HEAD'], ROOT))
    with tempfile.TemporaryDirectory(prefix='ranex-release-check-') as directory:
        clone = Path(directory) / 'repo'
        require(run(['git', 'clone', '--quiet', '--no-hardlinks', ROOT, clone], ROOT))
        require(run(['uv', 'sync', '--frozen'], clone))
        project = (clone / 'pyproject.toml').read_text()
        current = tomllib.loads(project)['project']['version']
        major, minor, patch = map(int, current.split('.'))
        epoch = str(yaml.safe_load((clone / 'governance/deps.yaml').read_text())['exclude_newer'])
        candidates = [f'{major}.{minor}.{patch + 1}rc1', f'{major}.{minor}.1000']
        for candidate in candidates:
            (clone / 'pyproject.toml').write_text(project.replace(
                f'version = "{current}"', f'version = "{candidate}"', 1))
            require(run(['uv', 'lock', '--exclude-newer', epoch], clone))
            require(run(['uv', 'sync', '--frozen'], clone))
            require(run(['uv', 'build', '--no-build-isolation', '--exclude-newer', epoch,
                         '--out-dir', out / candidate], clone))
            wheel, = (out / candidate).glob('*.whl')
            # The coverage-bearing source invocation below must be the actual
            # installed wheel's code, not a path alias for different versions.
            with zipfile.ZipFile(wheel) as package:
                source_matches = all(package.read(str(path.relative_to(ROOT / 'src'))) == path.read_bytes()
                                     for path in (ROOT / 'src/ranex').rglob('*.py'))
            if not source_matches:
                raise RuntimeError('candidate wheel source differs from the measured checkout')
            require(run(['uv', 'pip', 'install', '--python', clone / '.venv/bin/python',
                         '--no-deps', '--reinstall', wheel], clone))
            clean = dict(os.environ)
            for name in ('PYTHONPATH', 'PYTEST_PLUGINS', 'PYTEST_ADDOPTS',
                         'COVERAGE_PROCESS_START', 'COVERAGE_PROCESS_CONFIG', 'COVERAGE_FILE'):
                clean.pop(name, None)
            installed = require(run([clone / '.venv/bin/ranex', '--version'], Path(directory), clean))
            if installed != f'ranex {candidate}':
                raise RuntimeError('installed candidate version does not match its package')
            # Exercise the installed artifact against a different interpreter.
            # Declaring the controller's site-packages as PYTHONPATH silently
            # replaced system pytest 7.4.4 with controller pytest 9.1.1.
            subject = Path(directory) / f'application-{candidate}'
            subject.mkdir()
            subject_pytest = require(run(['/usr/bin/python3', '-c',
                'import pytest; print(pytest.__version__)'], subject, clean))
            controller_site = require(run([clone / '.venv/bin/python', '-c',
                'from pathlib import Path; import ranex; print(Path(ranex.__file__).parent.parent)'],
                subject, clean))
            (subject / 'test_environment.py').write_text(
                'import pytest, sys\ndef test_runtime_dependencies_are_preserved():\n'
                f'    assert pytest.__version__ == {subject_pytest!r}\n'
                f'    assert {controller_site!r} not in sys.path\n')
            (subject / '.gitignore').write_text('*.xml\nsuite_manifest.json\n__pycache__/\n.pytest_cache/\n')
            for command in (['git', 'init', '-q'], ['git', 'config', 'user.name', 'Installed probe'],
                            ['git', 'config', 'user.email', 'probe@example.invalid'],
                            ['git', 'add', '.'], ['git', 'commit', '-qm', 'pin the actual subject runtime']):
                require(run(command, subject, clean))
            suite = ['/usr/bin/python3', '-m', 'pytest', '-q', '-o', 'xfail_strict=true', '--junitxml=result.xml']
            require(run(suite, subject, clean))
            observer_modes = []
            for plugin in ([], ['-p', 'ranex.foundation.pytest_xpass'], ['-pranex.foundation.pytest_xpass']):
                output = require(run([clone / '.venv/bin/ranex', 'suite', 'freeze',
                    '--external-repository', subject, '--artifact', 'result.xml', '--output',
                    'suite_manifest.json', '--', *suite, *plugin], subject, clean))
                if 'run_exit=0' not in output:
                    raise RuntimeError('installed observer changed the subject runtime: ' + output)
                observer_modes.append(dict(plugin=plugin, subject_pytest=subject_pytest, stdout=output))
            measured = dict(os.environ, PYTHONPATH=os.pathsep.join((str(ROOT / 'src'),
                                      str(ROOT / 'tests/e2e/coverage'))))
            observed = require(run([clone / '.venv/bin/ranex', '--version'], ROOT, measured))
            refusal = run([clone / '.venv/bin/python', clone / 'tools/dogfood/release.py', 'version'],
                          ROOT, measured)
            if observed != installed or refusal.returncode != 1 or 'RELEASE-REFUSED:' not in refusal.stdout:
                raise RuntimeError('candidate release admission did not refuse the unsupported tag')
            results.append(dict(candidate=candidate, installed_version=installed,
                                source_matches=source_matches, observer_modes=observer_modes, release_refusal=refusal.stdout.strip(),
                                artifacts={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in (out / candidate).iterdir() if p.is_file()}))
        receipt = dict(kernel=kernel, scope='Real candidate builds and installed CLI, with byte-verified source coverage',
                       results=results)
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
