"""Frozen black-box journal journey: real CLI, real SQLite, named defect assertion."""

import json, os, re, sqlite3, subprocess, sys
from pathlib import Path
subject = Path(sys.argv[1])
env = {k:v for k,v in os.environ.items() if not k.startswith(('RANEX_', 'COVERAGE_'))}
env['PYTHONPATH'] = str(subject / 'src')
observations = []
def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)
def run(step, args):
    result = subprocess.run([sys.executable, '-m', 'ranex.cli.main', *args], cwd=subject, env=env, capture_output=True, text=True, timeout=45)
    observations.append(dict(step=step, argv=args, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return result
try:
    evaluation = run('create-real-journal', ['gate','evaluate','HEAD','--approver','probe-owner'])
    require(evaluation.returncode == 1, 'setup must record missing-evidence refusal')
    good = run('verify-intact-journal', ['journal','verify'])
    require(good.returncode == 0 and 'chain=verified' in good.stdout, 'intact journal did not verify')
    with sqlite3.connect(subject / 'governance/journal.sqlite3') as conn:
        seq, record = conn.execute('SELECT seq, record FROM evaluations ORDER BY seq LIMIT 1').fetchone()
        match = re.search(r'sha256:[0-9a-f]', record)
        require(match, 'no real digest recorded')
        index = match.end() - 1
        changed = record[:index] + ('1' if record[index] == '0' else '0') + record[index+1:]
        json.loads(changed)
        conn.execute('DROP TRIGGER evaluations_no_update')
        conn.execute('UPDATE evaluations SET record=? WHERE seq=?', (changed, seq))
    bad = run('reject-tampered-journal', ['journal','verify'])
    passed = bad.returncode == 1 and 'chain=invalid' in bad.stdout
    print(json.dumps(dict(status='MATCH' if passed else 'MISMATCH', failed_assertion=None if passed else 'reject-tampered-journal', observations=observations), sort_keys=True))
    sys.exit(0 if passed else 1)
except (RuntimeError, OSError, sqlite3.Error, subprocess.TimeoutExpired) as exc:
    print(json.dumps(dict(status='INFRASTRUCTURE-OR-SETUP-ERROR', error=str(exc), observations=observations), sort_keys=True))
    sys.exit(2)
