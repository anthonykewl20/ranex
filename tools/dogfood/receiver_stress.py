"""Stress the actual webhook CLI using a saved public GitHub pull request.

The input must be an unedited `gh api repos/OWNER/REPO/pulls/NUMBER` response.
Fresh local signing credentials authenticate replay traffic; no fabricated API
responds. Git fetch recovery, API outage, restart and receipt corruption use
real processes and files. Live installed GitHub App publication is unverified.
"""

import argparse
import concurrent.futures
import hashlib
import hmac
import http.client
import json
import os
import resource
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--pull-request", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=False)
PR = json.loads(args.pull_request.read_text())
SECRET = secrets.token_hex(32)
BODY = json.dumps({'action': 'reopened', 'installation': {'id': 1},
                   'repository': PR['base']['repo'], 'pull_request': PR}).encode()
IGNORED = BODY.replace(b'"action": "reopened"', b'"action": "closed"')
rows = []


def record(name, ok, facts):
    rows.append(dict(case=name, verified=ok, facts=facts))
    (OUT / 'receipt.json').write_text(json.dumps(dict(
        source=f"gh api repos/{PR['base']['repo']['full_name']}/pulls/{PR['number']}",
        pull_request_sha256=hashlib.sha256(args.pull_request.read_bytes()).hexdigest(),
        head_sha=PR['head']['sha'],
        scope='Real public PR replay through actual CLI; local HMAC and installation 1; live GitHub App publication UNVERIFIED',
        kernel=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        rows=rows), indent=2) + '\n')
    print(name, ok, facts, flush=True)
    if not ok:
        raise RuntimeError(name)


def request(port, delivery, body=IGNORED, *, path='/webhook', **headers):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        conn.request('POST', path, body, headers={
            'X-GitHub-Delivery': delivery, 'X-GitHub-Event': 'pull_request',
            'X-Hub-Signature-256': 'sha256=' + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest(),
            **headers})
        response = conn.getresponse()
        response.read()
        return response.status
    finally:
        conn.close()


with tempfile.TemporaryDirectory(prefix='ranex-real-pr-replay-') as directory, socket.socket() as api:
    root = Path(directory)
    repo = root / 'repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '--quiet', str(repo)], check=True)
    archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive', 'HEAD', 'governance'])
    subprocess.run(['tar', '-x', '-C', str(repo)], input=archive, check=True)
    subprocess.run(['git', '-C', str(repo), 'add', 'governance'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Ranex receiver replay',
                    '-c', 'user.email=ranex-replay@example.invalid',
                    'commit', '-qm', 'Actual Ranex governance for PR replay'], check=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = root / 'app.pem'
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    private.chmod(0o600)
    api.bind(('127.0.0.1', 0))  # Real unavailable API endpoint; never a fabricated API response.
    remote = root / 'remote'
    journal = repo / '.local/ranex/github/deliveries.jsonl'
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, (str(ROOT / 'src'), os.environ.get('PYTHONPATH')))),
                       RANEX_GITHUB_APP_ID='1', RANEX_GITHUB_APP_PRIVATE_KEY=str(private),
                       RANEX_GITHUB_WEBHOOK_SECRET=SECRET,
                       RANEX_GITHUB_API_ROOT=f'http://127.0.0.1:{api.getsockname()[1]}')

    @contextmanager
    def server(*, force_kill=False):
        with socket.socket() as selector:
            selector.bind(('127.0.0.1', 0))
            port = selector.getsockname()[1]
        with (OUT / 'server.log').open('a') as log:
            command = [sys.executable, '-m', 'ranex.cli.main', 'github', 'listen',
                       '--repository', str(repo), '--bind', f'127.0.0.1:{port}',
                       '--remote', str(remote), '--installation', '1',
                       '--repo', PR['base']['repo']['full_name'], '--approver', 'audit']
            process = subprocess.Popen(command, env=environment, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError('CLI exited: ' + (OUT / 'server.log').read_text())
                    try:
                        with socket.create_connection(('127.0.0.1', port), timeout=.1):
                            break
                    except OSError:
                        time.sleep(.05)
                yield port, process
            finally:
                if force_kill:
                    process.kill()
                else:
                    process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                    raise

    with server(force_kill=True) as (port, process):
        first = request(port, 'real-pr-recovery', BODY)
        first_entry = json.loads(journal.read_text().splitlines()[-1])
        remote.symlink_to(ROOT, target_is_directory=True)
        second = request(port, 'real-pr-recovery', BODY)
        second_entry = json.loads(journal.read_text().splitlines()[-1])
        record('real-git-remote-recovery', first == second == 500
               and first_entry['outcome'] == 'E-GITHUB-UNFETCHABLE-HEAD'
               and second_entry['outcome'] == 'E-GITHUB-API-REFUSED', [first_entry, second_entry])
        outcomes = []

        def deliver(index):
            delivery = f'real-pr-{index % 100}'
            for attempt in range(100):
                status = request(port, delivery)
                if status == 200:
                    return attempt, status
                if status != 503:
                    return attempt, status
                time.sleep(.005)
            return 100, status

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(deliver, range(1000)))
        entries = [json.loads(line) for line in journal.read_text().splitlines()]
        ignored = [e for e in entries if e['outcome'] == 'ignored']
        record('1000-concurrent-real-pr-replays', all(s == 200 for _, s in outcomes)
               and len(ignored) == 100, dict(requests=1000, completed_ids=len(ignored),
                                            busy_redeliveries=sum(a for a, _ in outcomes)))
        conflict = request(port, 'real-pr-0', BODY)
        record('same-id-different-authenticated-body', conflict == 409, conflict)

    with server() as (port, process):
        statuses = [request(port, f'real-pr-{i}') for i in range(100)]
        entries = [json.loads(line) for line in journal.read_text().splitlines()]
        record('sigkill-restart-retains-100-completions', all(s == 200 for s in statuses)
               and all(e['outcome'] == 'replayed' for e in entries[-100:]), len(statuses))
        conflict = request(port, 'real-pr-0', BODY)
        record('restart-retains-body-binding', conflict == 409, conflict)
        status = request(port, 'real-pr-recovery', BODY)
        record('sigkill-restart-retries-api-failure', status == 500
               and json.loads(journal.read_text().splitlines()[-1])['outcome'] == 'E-GITHUB-API-REFUSED', status)
        for iteration in range(5):
            sockets = [socket.create_connection(('127.0.0.1', port), timeout=2) for _ in range(32)]
            time.sleep(.25)
            status_file = Path(f'/proc/{process.pid}/status').read_text()
            threads = int(next(line.split()[1] for line in status_file.splitlines() if line.startswith('Threads:')))
            descriptors = len(list(Path(f'/proc/{process.pid}/fd').iterdir()))
            time.sleep(5.25)
            recovered = request(port, f'recovered-{iteration}')
            for client in sockets:
                client.close()
            record(f'saturation-{iteration}', threads <= 33 and descriptors < 80 and recovered == 200,
                   dict(opened=32, threads=threads, descriptors=descriptors, recovered=recovered))
        client = socket.create_connection(('127.0.0.1', port), timeout=2)
        start = time.monotonic()
        disconnected = False
        while time.monotonic() - start < 7:
            try:
                client.sendall(b'P')
            except OSError:
                disconnected = True
                break
            time.sleep(.1)
        client.close()
        elapsed = time.monotonic() - start
        record('trickle-client-wall-deadline', disconnected and elapsed < 6, dict(disconnected=disconnected, seconds=elapsed))
        record('healthy-after-trickle', request(port, 'after-trickle') == 200, 'HTTP 200')
        receipt_path = journal.parent / 'completed/real-pr-0.json'
        original = receipt_path.read_bytes()
        receipt_path.chmod(0o600)
        for mutation in (b'', b'[]', b'{}', b'{"fingerprint":42}'):
            receipt_path.write_bytes(mutation)
            refused = request(port, 'real-pr-0')
            receipt_path.write_bytes(original)
            recovered = request(port, 'real-pr-0')
            record('damaged-receipt-recovery', refused == 500 and recovered == 200,
                   dict(damaged_bytes=mutation.decode(), refused=refused, recovered=recovered))
        for name, changes, expected in (
            ('wrong-endpoint', {'path': '/missing'}, 404),
            ('negative-length', {'Content-Length': '-1'}, 400),
            ('oversized-length', {'Content-Length': '1048577'}, 413),
            ('ambiguous-transfer', {'Transfer-Encoding': 'chunked'}, 400),
            ('wrong-signature', {'X-Hub-Signature-256': 'sha256=' + '0' * 64}, 401),
            ('non-ascii-signature', {'X-Hub-Signature-256': 'é'}, 401),
        ):
            status = request(port, name, **changes)
            record(name, status == expected, dict(expected=expected, actual=status))
        record('malformed-delivery-id', request(port, 'invalid/id') == 400, 'HTTP 400')
        for index, damaged in enumerate((BODY[:-1], b'\xff' + BODY[1:])):
            status = request(port, f'damaged-pr-{index}', damaged)
            observed = json.loads(journal.read_text().splitlines()[-1])
            record('damaged-real-pr-payload', status == 200 and observed['outcome'] == 'E-GITHUB-BAD-EVENT',
                   dict(status=status, receipt=observed))
        saved_journal = journal.read_bytes()
        marker = journal.parent / 'spool-v2.json'
        saved_marker = marker.read_bytes()
        marker.unlink()
        receipt_path.unlink()  # Migration must rebuild a receipt from the actual legacy journal.
        journal.write_bytes(b'[]\n')
        refused = request(port, 'real-pr-0')
        journal.write_bytes(saved_journal)
        recovered = request(port, 'real-pr-0')
        record('legacy-spool-damage-recovery', refused == 500 and recovered == 200,
               dict(refused=refused, recovered=recovered))
        marker.chmod(0o600)
        marker.write_bytes(saved_marker)
        with server() as (other_port, _other_process):
            def multi_process_delivery(index):
                endpoint = port if index % 2 else other_port
                for _attempt in range(100):
                    answer = request(endpoint, f'real-pr-{index % 100}')
                    if answer != 503:
                        return answer
                    time.sleep(.005)
                return answer
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                statuses = list(pool.map(multi_process_delivery, range(200)))
            record('two-receivers-share-durable-state', all(s == 200 for s in statuses),
                   dict(requests=len(statuses), accepted=statuses.count(200)))
    with server() as (port, process):
        # Linux limits apply only to this receiver; no parent/other process limit changes.
        original_limit = resource.prlimit(process.pid, resource.RLIMIT_NPROC)
        time.sleep(.1)
        resource.prlimit(process.pid, resource.RLIMIT_NPROC, (1, original_limit[1]))
        refused = False
        try:
            try:
                request(port, 'thread-exhaustion')
            except (OSError, http.client.HTTPException):
                refused = True
        finally:
            resource.prlimit(process.pid, resource.RLIMIT_NPROC, original_limit)
        recovered = request(port, 'after-thread-exhaustion')
        record('real-thread-exhaustion-recovery', refused and recovered == 200,
               dict(refused=refused, recovered=recovered))
    (OUT / 'deliveries.jsonl').write_bytes(journal.read_bytes())
