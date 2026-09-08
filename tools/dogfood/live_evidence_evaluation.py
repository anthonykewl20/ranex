"""Real GitHub-origin webhooks and fresh upstream Six evidence.

Requires an explicitly prepared probe branch containing Six's source/tests,
committed governance and a frozen suite with declared platform skips. Observes
that trusted upstream code via the actual Ranex CLI; this is NOT unattended
execution of arbitrary contributor code. Never constructs or signs a webhook.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

from ranex.github_app.client import AppCredentials, GitHubClient, mint_app_jwt
from ranex.github_app.registration import load_stored_identity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--credentials-dir', type=Path, required=True)
    parser.add_argument('--worker-key', type=Path, required=True)
    parser.add_argument('--verdict-key', type=Path, required=True)
    parser.add_argument('--installation', type=int, required=True)
    parser.add_argument('--pull-request', type=int, help='resume an open probe PR on this branch')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--replace-listener-pid', type=int)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.repository.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    output = args.out.resolve()
    state = root / '.local/automatic-listener'
    identity = load_stored_identity(args.credentials_dir)
    credentials = AppCredentials(str(identity['app_id']), args.credentials_dir / 'app.pem',
                                 (args.credentials_dir / 'webhook-secret').read_text().strip())
    client = GitHubClient(credentials)
    records = []

    def record(phase, **values):
        records.append({'phase': phase, **values})
        (output / 'receipt.json').write_text(json.dumps({'scope': __doc__, 'records': records}, indent=2) + '\n')
        print(phase, json.dumps(values), flush=True)

    def operator_environment():
        subprocess.run(['gh', 'auth', 'switch', '-h', 'github.com', '-u', 'anthonykewl20'],
                       check=True, capture_output=True)
        token = subprocess.check_output(['gh', 'auth', 'token', '--hostname', 'github.com',
                                         '--user', 'anthonykewl20'], text=True).strip()
        environment = {**os.environ, 'GH_TOKEN': token}
        who = subprocess.check_output(['gh', 'api', 'user', '--jq', '.login'], env=environment, text=True).strip()
        assert who == 'anthonykewl20'
        return environment

    def api(method, path, payload=None):
        environment = operator_environment()
        argv = ['gh', 'api', '--method', method, path]
        if payload is not None:
            argv += ['--input', '-']
        result = subprocess.run(argv, env=environment, input=json.dumps(payload) if payload is not None else None,
                                capture_output=True, text=True, check=False, timeout=60)
        return result.returncode, json.loads(result.stdout)

    def git(*argv):
        return subprocess.check_output(['git', '-C', str(root), *argv], text=True).strip()

    def push():
        subprocess.run(['git', '-C', str(root), '-c', 'credential.helper=', '-c',
                        'credential.helper=!gh auth git-credential', 'push', 'origin', branch],
                       env=operator_environment(), capture_output=True, check=True, timeout=60)
        head = git('rev-parse', 'HEAD')
        remote = git('ls-remote', 'origin', f'refs/heads/{branch}').split()[0]
        assert remote == head
        return head

    def wait_for(head, conclusion, *, after_id=0):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if listener.poll() is not None:
                raise RuntimeError('receiver exited; inspect listener.log')
            runs = client.list_check_runs(args.installation, args.repo, head, check_name='ranex/acceptance')
            matches = [r for r in runs if r.get('conclusion') == conclusion and r.get('app', {}).get('id') == identity['app_id'] and r['id'] > after_id]
            if matches:
                latest = max(matches, key=lambda run: run['id'])
                record('check', head=head, conclusion=conclusion, id=latest['id'], url=latest['html_url'],
                       matching_checks=len(matches))
                return latest
            time.sleep(3)
        raise RuntimeError(f'no {conclusion} for {head}')

    def observe(expected):
        command = yaml.safe_load((root / 'governance/gates.yaml').read_bytes())['gates'][0]['required_claims'][0]['command']
        environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                       'PYTHONPATH': str(Path(__file__).resolve().parents[2] / 'src'),
                       'RANEX_SIGNING_KEY': str(args.worker_key)}
        result = subprocess.run([sys.executable, '-m', 'ranex.cli.main', 'run',
                                 '--external-repository', str(root), '--producer', 'worker',
                                 '--claim', 'tests-executed', '--', *command],
                                env=environment, capture_output=True, text=True, timeout=120, check=False)
        (output / f'observe-{len(records)}.log').write_text(result.stdout + result.stderr)
        assert result.returncode == expected, result.stdout + result.stderr
        evidence = json.loads((root / 'governance/evidence.json').read_bytes())[-1]
        record('observation', head=git('rev-parse', 'HEAD'), exit=result.returncode,
               suite=evidence['suite_results']['counts'])

    branch = git('branch', '--show-current')
    assert branch.startswith('live/'), 'use an explicit probe branch'
    replaced = None
    listener = None
    log = (output / 'listener.log').open('wb')
    if args.replace_listener_pid:
        proc = Path('/proc') / str(args.replace_listener_pid)
        argv = [x.decode() for x in (proc / 'cmdline').read_bytes().split(b'\0') if x]
        assert 'listen' in argv and 'github' in argv, 'replacement must be a Ranex receiver'
        environment = dict(x.decode().split('=', 1) for x in (proc / 'environ').read_bytes().split(b'\0') if x)
        replaced = (argv, environment, str((proc / 'cwd').resolve()))
        os.kill(args.replace_listener_pid, signal.SIGTERM)
        time.sleep(2)
    try:
        environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                       'PYTHONPATH': str(Path(__file__).resolve().parents[2] / 'src'),
                       'RANEX_GITHUB_APP_ID': str(identity['app_id']),
                       'RANEX_GITHUB_APP_PRIVATE_KEY': str(credentials.private_key_path),
                       'RANEX_GITHUB_WEBHOOK_SECRET': credentials.webhook_secret,
                       'RANEX_VERDICT_SIGNING_KEY': str(args.verdict_key)}
        argv = [sys.executable, '-m', 'ranex.cli.main', 'github', 'listen',
                '--bind', f'127.0.0.1:{args.port}', '--repo', args.repo,
                '--repository', str(root), '--installation', str(args.installation),
                '--approver', 'operator', '--state-dir', str(state.relative_to(root)), '--evaluate-evidence']
        listener = subprocess.Popen(argv, env=environment, stdout=log, stderr=log)
        for _ in range(30):
            try:
                with socket.create_connection(('127.0.0.1', args.port), timeout=1):
                    break
            except OSError:
                time.sleep(0.2)
        head = push()
        if args.pull_request is None:
            code, pr = api('POST', f'repos/{args.repo}/pulls', {
                'title': 'Live automatic evidence evaluation: upstream Six', 'head': branch,
                'base': 'main', 'body': 'Real GitHub webhook and fresh upstream test evidence acceptance exercise.'})
        else:
            code, pr = api('GET', f'repos/{args.repo}/pulls/{args.pull_request}')
            assert pr.get('state') == 'open' and pr['head']['ref'] == branch
            assert pr['head']['repo']['full_name'] == args.repo and pr['head']['sha'] == head
        assert code == 0, pr
        number = pr['number']
        record('pull-request', number=number, url=pr['html_url'], head=head)
        wait_for(head, 'action_required')
        code, refusal = api('PUT', f'repos/{args.repo}/pulls/{number}/merge', {'sha': head})
        assert code != 0 and not refusal.get('merged'), refusal
        record('merge-refused-before-evidence', response=refusal)
        observe(0)
        wait_for(head, 'success')
        original = (root / 'six.py').read_text()
        # Break a real upstream API without changing its tests or policy.
        assert 'return s.encode("latin-1")' in original
        (root / 'six.py').write_text(original.replace('return s.encode("latin-1")', 'return b"broken"', 1))
        git('add', 'six.py')
        git('commit', '-qm', 'test: break Six bytes conversion to verify merge refusal')
        head = push()
        stale = wait_for(head, 'failure')  # old source's passing evidence must fail
        observe(1)
        wait_for(head, 'failure', after_id=stale['id'])
        code, refusal = api('PUT', f'repos/{args.repo}/pulls/{number}/merge', {'sha': head})
        assert code != 0 and not refusal.get('merged'), refusal
        record('merge-refused-broken-source', response=refusal)
        (root / 'six.py').write_text(original + '\n# Live acceptance recovery: source restored.\n')
        git('add', 'six.py')
        git('commit', '-qm', 'test: restore Six and require fresh evidence')
        head = push()
        wait_for(head, 'failure')
        observe(0)
        wait_for(head, 'success')
        # Correlate receiver GUIDs with GitHub's own delivery log. No locally
        # constructed webhook can supply this independent origin receipt.
        entries = [json.loads(line) for line in (state / 'deliveries.jsonl').read_text().splitlines()]
        ids = {row['delivery'] for row in entries if 'delivery' in row}
        deliveries = client._request('GET', '/app/hook/deliveries?per_page=100', token=mint_app_jwt(credentials))
        matched = [dict(guid=d['guid'], event=d['event'], status_code=d['status_code'])
                   for d in deliveries if d['guid'] in ids]
        assert len(matched) >= 3, matched
        record('github-origin-deliveries', deliveries=matched)
        # GitHub's merge-enforcement view can lag its Checks API. Retry only
        # the same explicitly tested SHA and keep each refusal as evidence.
        deadline = time.monotonic() + 120
        while True:
            code, merged = api('PUT', f'repos/{args.repo}/pulls/{number}/merge', {'sha': head})
            if code == 0 and merged.get('merged'):
                break
            record('merge-propagation-wait', response=merged)
            if merged.get('status') != '405' or time.monotonic() >= deadline:
                raise AssertionError(merged)
            time.sleep(5)
        record('merge-accepted', response=merged, verified=True)
    finally:
        if listener is not None:
            listener.terminate()
            listener.wait(timeout=10)
        if replaced is not None:
            argv, environment, cwd = replaced
            with (output / 'restored-listener.log').open('wb') as restored_log:
                restored = subprocess.Popen(argv, env=environment, cwd=cwd,
                                            stdout=restored_log, stderr=restored_log, start_new_session=True)
            record('restored-development-receiver', pid=restored.pid)
        log.close()


if __name__ == '__main__':
    main()
