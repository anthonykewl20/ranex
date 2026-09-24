"""Retain live HTTP/database acceptance observations from the installed CLI.

Real Docker containers, real PostgreSQL, real PostgREST HTTP traffic against
exact Git-bound candidates. The observer is the trusted controller; candidate
SQL never runs outside the database container and candidate scripts never run
at all. Receipts are independently retained observations with fail-closed
outcomes, not approval, verdict admission or a product PASS.

Every expectation runs three times on identical input. Deterministic outputs
(the HTTP observation rows) must be byte-identical across repetitions; the
completion status is VERIFIED only when the observed outcome matches the
frozen expectation in all three runs.
"""

import argparse, atexit, copy, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

source = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(source / 'src'))
from ranex.foundation.specification_abc import canonical_payload_bytes

parser = argparse.ArgumentParser(description='Live PostgREST/PostgreSQL acceptance qualification through the installed ranex CLI')
parser.add_argument('--output', type=Path, required=True, help='new external output directory')
args = parser.parse_args()
out = args.output.resolve()
if out == source or source in out.parents:
    parser.error('output must be outside the Ranex checkout')
out.mkdir(mode=0o700)

logs = []
atexit.register(lambda: (out / 'commands.json').write_bytes(canonical_payload_bytes(logs)))
expectations = []


def require(condition, detail):
    if not condition:
        (out / 'failure.json').write_bytes(canonical_payload_bytes({'status': 'EXPERIMENT-FAILED', 'detail': str(detail)}))
        raise RuntimeError(detail)


def command(argv, cwd=source, env=None, timeout=900):
    started = time.monotonic()
    p = subprocess.run([str(a) for a in argv], cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout)
    logs.append(dict(argv=[str(a) for a in argv], cwd=str(cwd), exit=p.returncode,
                     wall_clock_ms=int((time.monotonic() - started) * 1000),
                     stdout_sha256=hashlib.sha256(p.stdout.encode()).hexdigest(),
                     stderr_sha256=hashlib.sha256(p.stderr.encode()).hexdigest()))
    return p


def digest(raw: bytes) -> str:
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


# --- installed console script and host facts ---------------------------------
ranex = source / '.venv/bin/ranex'
require(ranex.exists() and os.access(ranex, os.X_OK), 'installed ranex console script missing (run: uv sync --frozen)')
installed = command([ranex, 'specification', 'observe-http', '--help'])
require(installed.returncode == 0 and 'observe-http' in installed.stdout, installed.stderr)
observer_bytes = (source / 'src/ranex/cli/http_observer.py').read_bytes()
observer_digest = digest(observer_bytes)

PG = 'sha256:e013e867e712fec275706a6c51c966f0bb0c93cfa8f51000f85a15f9865a28cb'
API = 'sha256:5922bde07147b82b1c9d8f749e48c1e5b99ebb233f3888bb7ab65f07cf4ac82d'
facts = {'ranex_console_script': str(ranex),
         'docker_server_version': command(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip(),
         'kernel': command(['uname', '-r']).stdout.strip()}
for key, image in (('postgres_image', PG), ('api_image', API)):
    observed = command(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'])
    require(observed.returncode == 0, f'pinned image not installed: {image}')
    facts[key] = observed.stdout.strip()

SCHEMA = '''CREATE ROLE authenticator LOGIN NOINHERIT PASSWORD 'experiment-api';
CREATE ROLE alice NOLOGIN; CREATE ROLE bob NOLOGIN; CREATE ROLE anon NOLOGIN;
GRANT alice,bob,anon TO authenticator;
CREATE SCHEMA api; GRANT USAGE ON SCHEMA api TO alice,bob,anon;
CREATE TABLE api.orders(id serial PRIMARY KEY,owner name NOT NULL DEFAULT current_user,item text NOT NULL);
ALTER TABLE api.orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY isolation ON api.orders USING(owner=current_user) WITH CHECK(owner=current_user);
GRANT SELECT,INSERT ON api.orders TO alice,bob;
GRANT USAGE ON SEQUENCE api.orders_id_seq TO alice,bob;
'''


def step(ident, method, path, role, body, expect, capture=None):
    return dict(id=ident, request=dict(method=method, path=path, role=role, body=body),
                expect=[dict(path=selector, equals=value) for selector, value in expect],
                capture=capture or {})


def journey_steps():
    return [
        step('invalid-token', 'GET', '/orders', 'invalid', None, [(['status'], 401)]),
        step('invalid-order', 'POST', '/orders', 'alice', {'item': None}, [(['status'], 400)]),
        step('create-order', 'POST', '/orders', 'alice', {'item': 'acceptance order'},
             [(['status'], 201), (['json', 0, 'owner'], 'alice'), (['json', 0, 'item'], 'acceptance order')],
             {'order_id': ['json', 0, 'id']}),
        step('owner-read', 'GET', '/orders?id=eq.{order_id}', 'alice', None,
             [(['status'], 200), (['json'], [{'id': {'var': 'order_id'}, 'owner': 'alice', 'item': 'acceptance order'}])]),
        step('tenant-isolation', 'GET', '/orders?id=eq.{order_id}', 'bob', None, [(['status'], 200), (['json'], [])]),
        step('forged-owner', 'POST', '/orders', 'bob', {'owner': 'alice', 'item': 'forged'}, [(['status'], 403)]),
        dict(id='restart-application', control='restart-app'),
        step('application-persistence', 'GET', '/orders?id=eq.{order_id}', 'alice', None,
             [(['status'], 200), (['json', 0, 'id'], {'var': 'order_id'})]),
        dict(id='stop-database', control='stop-db'),
        step('dependency-unavailable', 'GET', '/orders', 'alice', None, [(['status'], 503)]),
        dict(id='start-database', control='start-db'),
        step('database-persistence', 'GET', '/orders?id=eq.{order_id}', 'alice', None,
             [(['status'], 200), (['json', 0, 'id'], {'var': 'order_id'})]),
    ]


def profile(steps=None, repetitions=3, controls=None):
    return dict(version='postgrest-http-v1', observer_digest=observer_digest,
                postgres_image=PG, api_image=API, schema='product/schema.sql',
                timeout_seconds=20, max_body_bytes=65536, repetitions=repetitions,
                controls=controls if controls is not None else [
                    dict(id='remove-isolation', old='USING(owner=current_user)', new='USING(true)', fails='tenant-isolation')],
                steps=steps if steps is not None else journey_steps())


def fresh_subject(directory, frozen_profile):
    """Freeze probes on a fresh real Git candidate; return repo, bundle and B pin."""
    directory.mkdir(parents=True, exist_ok=True)
    root = directory / 'subject'
    root.mkdir()
    command(['git', 'init', '-q', root])
    command(['git', '-C', root, 'config', 'user.email', 'observer@example.invalid'])
    command(['git', '-C', root, 'config', 'user.name', 'Observer'])
    (root / 'acceptance').mkdir()
    (root / 'product').mkdir()
    (root / 'acceptance/http.json').write_bytes(canonical_payload_bytes(frozen_profile))
    (root / 'product/schema.sql').write_text('SELECT 1;\n')
    command(['git', '-C', root, 'add', '.'])
    command(['git', '-C', root, 'commit', '-qm', 'frozen observer profile before product work'])
    vectors = json.loads((source / 'tests/contract/fixtures/specification/abc-v1-vectors.json').read_bytes())
    packet = directory / 'A.json'
    packet.write_bytes(canonical_payload_bytes(vectors['triple']['a']))
    argv_file = directory / 'argv.json'
    argv_file.write_bytes(canonical_payload_bytes(['ranex', 'specification', 'observe-http', '--profile', 'acceptance/http.json']))
    bundle = directory / 'bundle'
    frozen = command([ranex, 'specification', 'freeze-probes', '--external-repository', root,
                      '--spec-packet', packet, '--invocation', argv_file,
                      '--root', 'acceptance', '--output', bundle])
    require(frozen.returncode == 0, frozen.stderr)
    return root, bundle, json.loads(frozen.stdout)['manifest_digest']


def commit_product(root, schema_text, message):
    (root / 'product/schema.sql').write_text(schema_text)
    command(['git', '-C', root, 'commit', '-qam', message])


def observe(label, repeat, root, bundle, pin):
    """Run the installed observer once; retain raw output; return the receipt."""
    directory = out / 'runs' / f'{label}-{repeat}'
    directory.parent.mkdir(parents=True, exist_ok=True)
    argv = [ranex, 'specification', 'observe-http', '--external-repository', root,
            '--bundle', bundle, '--manifest-digest', pin,
            '--profile', 'acceptance/http.json', '--output', directory]
    started = time.monotonic()
    result = command(argv)
    wall_ms = int((time.monotonic() - started) * 1000)
    receipt_bytes = (directory / 'receipt.json').read_bytes() if (directory / 'receipt.json').exists() else b''
    receipt = json.loads(receipt_bytes) if receipt_bytes else None
    expectations.append({
        'expectation': label, 'repeat': repeat, 'argv': [str(a) for a in argv],
        'cwd': str(source), 'exit_code': result.returncode,
        'input_digests': {'manifest_digest': pin,
                          'observer_sha256': observer_digest.split(':', 1)[1],
                          'candidate_commit': None if receipt is None else receipt.get('candidate_commit')},
        'output_digest': digest(receipt_bytes) if receipt_bytes else None,
        'wall_clock_ms': wall_ms,
        'stdout_digest': digest(result.stdout.encode()),
        'stderr_tail': result.stderr[-2000:],
        'status': receipt.get('status') if receipt else 'UNVERIFIED',
    })
    return result, receipt


def classify(result, receipt, wanted_status, wanted_assertion=None):
    """Map one observed run onto the completion-contract status vocabulary."""
    entry = expectations[-1]
    if receipt is None:
        entry['status'] = 'UNVERIFIED'
    elif receipt.get('status') == wanted_status and (wanted_assertion is None
            or receipt.get('failed_assertion') == wanted_assertion):
        entry['status'] = 'VERIFIED'
    elif result.returncode == 0:
        entry['status'] = 'FALSE-PASS'
    else:
        entry['status'] = 'GAP'
    return entry['status']


def deterministic_subset(receipt, journey_ids):
    """Outcome fields and journey-step observations that must repeat byte-identically.

    Controller readiness probes are excluded: PostgREST can answer transient
    503 connection-refused probes until its database pool is warm, and the
    observer correctly retries them under the frozen deadline while retaining
    every probe as raw evidence. Their count is timing, not product behaviour;
    every frozen journey step is compared exactly.
    """
    if receipt is None:
        return None
    return canonical_payload_bytes({
        'status': receipt.get('status'), 'calibrated': receipt.get('calibrated'),
        'failed_assertion': receipt.get('failed_assertion'), 'failed_control': receipt.get('failed_control'),
        'schema_sha256': receipt.get('schema_sha256'),
        'trials': [{'status': t['status'], 'failed_assertion': t['failed_assertion'],
                    'control': t['control'],
                    'observations': [o for o in t['observations'] if o['id'] in journey_ids]}
                   for t in receipt.get('trials', [])]})


# --- expectation 1: good candidate is observed matching, calibrated, 3x -------
JOURNEY_IDS = {step['id'] for step in journey_steps()}
good = out / 'good'
root, bundle, pin = fresh_subject(good, profile())
commit_product(root, SCHEMA, 'working product with tenant isolation')
receipts = []
for repeat in range(3):
    result, receipt = observe('good', repeat, root, bundle, pin)
    require(classify(result, receipt, 'OBSERVED-MATCH') == 'VERIFIED',
            f'good candidate run {repeat} did not observe a match: {result.stdout[-500:]} {result.stderr[-500:]}')
    require(receipt['candidate_commit'] == command(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip(),
            'observer did not bind the exact candidate commit')
    require(len(receipt['trials']) == 6 and not receipt['cleanup_errors'] and receipt['calibrated'] is True,
            'calibration shape changed')
    receipts.append(receipt)
fingerprint = deterministic_subset(receipts[0], JOURNEY_IDS)
for repeat in (1, 2):
    require(deterministic_subset(receipts[repeat], JOURNEY_IDS) == fingerprint,
            f'deterministic outputs differ across identical good runs at repeat {repeat}')
expectations.append({'expectation': 'good-determinism', 'repeat': None,
                     'detail': 'byte-identical status/calibration/journey-step observations across 3 identical runs (readiness probes excluded)',
                     'input_digests': {'manifest_digest': pin},
                     'output_digest': digest(fingerprint), 'status': 'VERIFIED'})

# --- expectation 2: committed known-bad candidate is observed mismatching -----
commit_product(root, SCHEMA.replace('USING(owner=current_user)', 'USING(true)'),
               'known-bad product: tenant isolation removed')
for repeat in range(3):
    result, receipt = observe('bad', repeat, root, bundle, pin)
    require(classify(result, receipt, 'OBSERVED-MISMATCH', 'tenant-isolation') == 'VERIFIED',
            f'known-bad candidate run {repeat} was not rejected at tenant-isolation: {result.stdout[-500:]}')

# --- expectation 3: calibration refusals, 3x each ------------------------------
for label, replacement, fails, trial_status in (
        ('surviving-control', 'USING((owner=current_user))', 'tenant-isolation', 'OBSERVED-MATCH'),
        ('compile-error', 'USING(', 'tenant-isolation', 'OBSERVATION-ERROR'),
        ('wrong-assertion', 'USING(true)', 'invalid-token', 'OBSERVED-MISMATCH'),
):
    directory = out / label
    revised = profile(repetitions=1)
    revised['controls'][0].update(new=replacement, fails=fails)
    candidate, frozen, digest_pin = fresh_subject(directory, revised)
    commit_product(candidate, SCHEMA, 'working product')
    for repeat in range(3):
        result, receipt = observe(label, repeat, candidate, frozen, digest_pin)
        require(classify(result, receipt, 'CALIBRATION-FAILED') == 'VERIFIED',
                f'{label} run {repeat} was not refused: {result.stdout[-500:]}')
        require(receipt['trials'][0]['status'] == 'OBSERVED-MATCH'
                and receipt['trials'][1]['status'] == trial_status
                and receipt['failed_control'] == 'remove-isolation',
                f'{label} refusal shape changed')

# --- retained subject bundle and summary --------------------------------------
command(['git', '-C', root, 'bundle', 'create', '-q', out / 'subject.bundle', 'HEAD'])
statuses = [e['status'] for e in expectations]
summary = {
    'version': 'live-observer-proof-v1',
    'result': 'VERIFIED' if all(s == 'VERIFIED' for s in statuses) else 'NOT-VERIFIED',
    'expectation_statuses': statuses,
    'expectations': expectations,
    'host_facts': facts,
    'limits': [
        'Trusted Linux controller and Docker daemon; candidate SQL only in the database container',
        'PostgREST/PostgreSQL profile with controlled test inputs; not production or browser evidence',
        'Observations with fail-closed outcomes; not approval, verdict admission or product PASS',
    ],
}
(out / 'summary.json').write_bytes(canonical_payload_bytes(summary))
print(json.dumps({'result': summary['result'], 'expectations': len(expectations),
                  'statuses': statuses}))
