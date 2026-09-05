"""Run upstream Six with real pytest, refuse its mounted in-tree alias, recover.

The executable is the installed system pytest artifact, never an authored test
double. Each mounted refusal must identify the same file, not merely exit 2.
Run sequentially with other governed/confinement journeys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import external_proof as proof
import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    results = []
    with tempfile.TemporaryDirectory(prefix='ranex-six-executable-') as directory:
        scratch = Path(directory)
        identity = proof.provision_kernel(scratch, ROOT, 'HEAD')
        repo, external = proof.clone_external(scratch, proof.EXTERNAL_URL, proof.EXTERNAL_REV)
        baseline = proof.measure_baseline(repo, scratch)
        setup = proof.onboard_governance(scratch / 'kernel', repo, scratch, 'HEAD', baseline['passing'], 0)
        installed = Path('/usr/bin/pytest')
        outside = scratch / 'pytest'
        shutil.copyfile(installed, outside)
        outside.chmod(0o755)
        command = [str(outside), *setup['argv'][3:]]
        catalog = repo / 'governance/gates.yaml'
        gates = yaml.safe_load(catalog.read_bytes())
        gates['gates'][0]['required_claims'][0]['command'] = command
        catalog.write_text(yaml.safe_dump(gates, sort_keys=False))
        evidence = repo / 'governance/evidence.json'

        def commit(message):
            for arguments in [('add', '-A'), ('commit', '-qm', message)]:
                response = proof._git(repo, *arguments)
                if response.returncode:
                    raise RuntimeError(response.stderr)

        def cli(*arguments, mounted=False):
            argv = [str(scratch / 'kernel/.venv/bin/python'), '-m', 'ranex.cli.main', *arguments]
            if mounted:
                argv = ['bwrap', '--dev-bind', '/', '/', '--bind', str(inside), str(outside),
                        '--', 'sh', '-c', 'stat -c "IDENTITY %d %i %h" "$1" "$2"; shift 2; exec "$@"',
                        'sh', str(inside), str(outside), *argv]
            response = subprocess.run(argv, cwd=repo, env=proof._kernel_env(repo, setup['key']),
                                      capture_output=True, text=True, check=False, timeout=900)
            commands.append(dict(argv=argv, exit=response.returncode, stdout=response.stdout,
                                 stderr=response.stderr, mounted=mounted))
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
            return response

        def passing(phase):
            run = cli('run', '--producer', proof.PRODUCER, '--claim', 'tests-executed', '--', *command)
            gate = cli('gate', 'evaluate', 'HEAD', '--approver', proof.APPROVER)
            if run.returncode or gate.returncode or not gate.stdout.startswith('PASS'):
                raise RuntimeError(run.stdout + run.stderr + gate.stdout + gate.stderr)
            record = json.loads(evidence.read_bytes())[0]
            if record['suite_results']['counts']['passed'] != setup['selected']:
                raise RuntimeError('the actual upstream passing test set did not execute')
            shutil.copyfile(evidence, out / f'{phase}-evidence.json')
            results.append(dict(phase=phase, verified=True, passed=setup['selected']))

        commit('govern the actual installed pytest executable by its explicit path')
        passing('pristine')
        inside = repo / 'tools/pytest'
        inside.parent.mkdir(exist_ok=True)
        shutil.copyfile(outside, inside)
        inside.chmod(0o755)
        commit('retain the actual pytest artifact for the mounted alias check')
        evidence.unlink()
        for iteration in range(10):
            response = cli('run', '--producer', proof.PRODUCER, '--claim', 'tests-executed',
                           '--', *command, mounted=True)
            identities = [line for line in response.stdout.splitlines() if line.startswith('IDENTITY ')]
            ok = (len(identities) == 2 and identities[0] == identities[1]
                  and identities[0].split()[-1] == '1' and response.returncode == 2
                  and 'same file as' in response.stderr and not evidence.exists())
            results.append(dict(phase='mounted', iteration=iteration, verified=ok, identities=identities))
            if not ok:
                raise RuntimeError(response.stdout + response.stderr)
        passing('recovered')
        receipt = dict(kernel=identity, external=external, baseline=baseline, results=results,
                       executable=dict(path=str(installed), sha256=hashlib.sha256(installed.read_bytes()).hexdigest()),
                       scope='Real upstream tests and installed pytest; ten actual bind mounts with identity-specific refusal')
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        for name in ('producers.yaml', 'suite_manifest.json', 'gates.yaml'):
            shutil.copyfile(repo / 'governance' / name, out / name)
        print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
