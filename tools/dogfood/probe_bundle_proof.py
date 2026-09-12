"""Retain actual CLI observations from three baseline/known-bad repetitions.

No model, mocks or internal candidate imports. This experiment does not provide
hostile-process confinement or admit its receipts as product verdict evidence.
"""

import argparse, atexit, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
source = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(source / 'src'))
from ranex.foundation.specification_abc import canonical_payload_bytes
parser = argparse.ArgumentParser(description='Real frozen-probe calibration against Ranex journal verification')
parser.add_argument('--output', type=Path, required=True, help='new external output directory')
args = parser.parse_args()
out = args.output.resolve()
if out == source or source in out.parents:
    parser.error('output must be outside the Ranex checkout')
out.mkdir(mode=0o700)
shutil.copyfile(source / 'tools/dogfood/probe_bundle_journal.py', out / 'journal_probe.py')
subject = out / 'subject'
logs = []
atexit.register(lambda: (out / 'commands.json').write_bytes(canonical_payload_bytes(logs)))
def require(condition, detail):
    if not condition:
        (out / 'failure.json').write_bytes(canonical_payload_bytes({'status':'EXPERIMENT-FAILED','detail':str(detail)}))
        raise RuntimeError(detail)
def command(args, cwd=source, env=None):
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True, timeout=90)
    logs.append(dict(argv=[str(a) for a in args], cwd=str(cwd), exit=p.returncode, stdout=p.stdout, stderr=p.stderr))
    return p
def git(*args):
    p = command(['git','-C',subject,*args])
    require(p.returncode == 0, p.stderr)
    return p.stdout.strip()
require(command(['git','clone','--quiet',source,subject]).returncode == 0, 'subject clone failed')
git('config','user.email','acceptance-experiment@example.invalid')
git('config','user.name','Acceptance experiment')
(subject / 'acceptance').mkdir()
shutil.copyfile(out / 'journal_probe.py', subject / 'acceptance/journal_probe.py')
git('add','acceptance/journal_probe.py')
git('commit','-qm','freeze real journal acceptance probe before product mutation')
base = git('rev-parse','HEAD')
packet = dict(version='spec-packet-v1', domain='ranex-live-journal', task='journal-integrity', revision=1,
 semantics=['An intact real evaluation journal verifies; a parseable out-of-band record modification must be rejected.'],
 scope={'include':['src/'], 'exclude':['acceptance/']}, answers={},
 observable_outcomes=['intact journal exit 0 with chain=verified','tampered journal exit 1 with chain=invalid'],
 non_goals=['HTTP/UI acceptance','hostile same-UID confinement','production sign-off'],
 oracle_provenance={'intact':'requirement','tampered':'requirement'},
 ids={'question':[], 'rule':['journal-integrity-rule'], 'transition':[], 'outcome':['intact','tampered'], 'error':[], 'test':['journal-live'], 'mapping':['journal-workflow']})
(out / 'A.json').write_bytes(canonical_payload_bytes(packet))
argv = [sys.executable, 'acceptance/journal_probe.py', str(subject)]
(out / 'argv.json').write_bytes(canonical_payload_bytes(argv))
controller = [sys.executable, '-m', 'ranex.cli.main', 'specification']
env = dict(os.environ, PYTHONPATH=str(source / 'src'))
frozen = command(controller + ['freeze-probes','--external-repository',subject,'--spec-packet',out/'A.json','--invocation',out/'argv.json','--root','acceptance','--output',out/'bundle'], env=env)
require(frozen.returncode == 0, frozen.stderr)
identity = json.loads(frozen.stdout)['manifest_digest']
product = subject / 'src/ranex/cli/main.py'
text = product.read_text()
old = 'verified = Journal(journal_path).verify(expected_head=expected_head)'
require(text.count(old) == 1, 'known-bad mutation target changed')
product.write_text(text.replace(old, 'verified = True  # known-bad calibration: bypass journal verification'))
git('add','src/ranex/cli/main.py')
git('commit','-qm','known-bad product: bypass real journal verification')
mutant = git('rev-parse','HEAD')
trials = []
for repeat in range(3):
    for label, commit in [('baseline',base),('known-bad',mutant)]:
        git('checkout','--detach',commit)
        for path in (subject / 'governance').glob('journal.sqlite3*'):
            path.unlink()
        checked = command(controller + ['check-probes','--external-repository',subject,'--bundle',out/'bundle','--manifest-digest',identity], env=env)
        require(checked.returncode == 0, checked.stderr)
        observed = command(argv, cwd=out/'bundle/probes')
        data = json.loads(observed.stdout)
        trials.append(dict(repeat=repeat, candidate=commit, kind=label, probe_exit=observed.returncode, result=data))
        if label == 'baseline':
            require(observed.returncode == 0 and data['status'] == 'MATCH', observed.stdout)
        else:
            require(observed.returncode == 1 and data['failed_assertion'] == 'reject-tampered-journal', observed.stdout)
(out / 'commands.json').write_bytes(canonical_payload_bytes(logs))
receipt = dict(version='ranex-live-probe-experiment-v1', kernel_commit=command(['git','rev-parse','HEAD']).stdout.strip(), base_commit=base, mutant_commit=mutant, manifest_digest=identity,
 probe_sha256=hashlib.sha256((out/'bundle/probes/acceptance/journal_probe.py').read_bytes()).hexdigest(),
 status='VERIFIED-BOUNDED-EXPERIMENT', trials=trials,
 limitations=['Prototype orchestration, not ranex prove or verdict admission', 'Observer and candidate share trusted host UID and interpreter; no hostile isolation claim', 'Tests one journal workflow only; no HTTP/database service or browser acceptance claim'])
(out / 'receipt.json').write_bytes(canonical_payload_bytes(receipt))
print(json.dumps(dict(status=receipt['status'], repeats=3, baseline_matches=sum(t['kind']=='baseline' and t['probe_exit']==0 for t in trials), known_bad_named_failures=sum(t['kind']=='known-bad' and t['probe_exit']==1 for t in trials), receipt=str(out/'receipt.json')), sort_keys=True))
