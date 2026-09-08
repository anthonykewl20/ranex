"""Replay a real GitHub PR through HTTP, restart recovery and live App publication.

Uses an existing operator clone and its trusted signed verdicts. Publishes one
check on the explicitly selected repository/head. The HTTP payload is assembled
from the current GitHub PR response and locally HMAC-signed: this is not proof
of a fresh GitHub-originated webhook or a new governed test observation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import threading
import uuid
from http.server import HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml

from ranex.bootstrap.composition import catalog_digest_for
from ranex.github_app.acceptance import resolve_acceptance
from ranex.github_app.binding import bind_pr_head, fetch_pr_head
from ranex.github_app.client import AppCredentials, GitHubClient
from ranex.github_app.receiver import ReceiverConfig, _ReceiverState, build_handler, drain_spool
from ranex.github_app.registration import load_stored_identity
from ranex.github_app.webhook import delivery_signature


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-repository', type=Path, required=True)
    parser.add_argument('--credentials-dir', type=Path, required=True)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--installation', type=int, required=True)
    parser.add_argument('--pull-request', type=int, required=True)
    parser.add_argument('--approver', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source = args.operator_repository.resolve()
    identity = load_stored_identity(args.credentials_dir)
    secret = (args.credentials_dir / 'webhook-secret').read_text().strip()
    client = GitHubClient(AppCredentials(str(identity['app_id']), args.credentials_dir / 'app.pem', secret))
    app = client.app_identity()
    assert app['id'] == identity['app_id']
    token = client.installation_token(args.installation)
    pr = client._request('GET', f'/repos/{args.repo}/pulls/{args.pull_request}', token=token)
    assert pr['base']['repo']['full_name'] == args.repo
    head = pr['head']['sha']
    body = json.dumps({'action': 'reopened', 'installation': {'id': args.installation},
                       'repository': pr['base']['repo'], 'pull_request': pr}).encode()
    (args.out / 'pull-request.json').write_text(json.dumps(pr, indent=2) + '\n')
    delivery = 'audit-recovery-' + str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix='ranex-live-recovery-') as temporary:
        clone = Path(temporary) / 'clone'
        subprocess.run(['git', 'clone', '--quiet', str(source), str(clone)], check=True)
        remote = f'https://github.com/{args.repo}.git'
        fetch_pr_head(clone, remote, head)
        producers = yaml.safe_load((source / 'governance/producers.yaml').read_text())
        config = ReceiverConfig(
            repo_root=clone, remote=remote, verdicts_dir=source / 'governance/verdicts',
            keyring={producers['verdict_signer']['id']: producers['verdict_signer']['public_key']},
            gate_id='landing', catalog_digest=catalog_digest_for((source / 'governance/gates.yaml').read_bytes()),
            approver_id=args.approver, webhook_secret=secret,
            allowlist=frozenset({(args.installation, args.repo)}), client=client,
            state_dir=args.out.resolve() / 'state',
        )
        binding = bind_pr_head(clone, head)
        acceptance = resolve_acceptance(config.verdicts_dir, binding, config.keyring,
                                        gate_id=config.gate_id, catalog_digest=config.catalog_digest,
                                        approver_id=config.approver_id)
        assert acceptance.publishable and acceptance.record['verdict'] == 'PASS', acceptance.code
        state = _ReceiverState()
        state.lock.acquire()  # Actual pipeline contention, no mocked methods.
        server = HTTPServer(('127.0.0.1', 0), build_handler(config, state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f'http://127.0.0.1:{server.server_port}/webhook', data=body, headers={
                'X-Hub-Signature-256': delivery_signature(secret, body),
                'X-GitHub-Delivery': delivery, 'X-GitHub-Event': 'pull_request',
            })
            try:
                urlopen(request, timeout=10)
            except HTTPError as error:
                status = error.code
                error.close()
            else:
                raise AssertionError('busy pipeline was not refused')
            assert status == 503
            assert (config.state_dir / 'spool' / f'{delivery}.json').exists()
        finally:
            state.lock.release()
            server.shutdown()
            thread.join()
            server.server_close()
        # New receiver state after the HTTP server has stopped; no redelivery.
        drained = drain_spool(config, _ReceiverState())
        assert drained == {delivery: 200}, drained
        checks = client.list_check_runs(args.installation, args.repo, head, check_name='ranex/acceptance')
        matching = [run for run in checks if run.get('external_id') == delivery]
        assert len(matching) == 1 and matching[0]['conclusion'] == 'success'
        assert matching[0]['app']['id'] == app['id']
        assert drain_spool(config, _ReceiverState()) == {}
        repeated = client.list_check_runs(args.installation, args.repo, head, check_name='ranex/acceptance')
        assert len([run for run in repeated if run.get('external_id') == delivery]) == 1
        receipt = {
            'kernel': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'scope': __doc__, 'repo': args.repo, 'head': head, 'app_id': app['id'],
            'app_owner': app['owner']['login'], 'delivery': delivery, 'http_status': status,
            'recovery_status': drained[delivery], 'check_id': matching[0]['id'],
            'check_url': matching[0]['html_url'], 'conclusion': matching[0]['conclusion'],
            'second_drain_duplicate_count': 0, 'verified': True,
        }
        (args.out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
