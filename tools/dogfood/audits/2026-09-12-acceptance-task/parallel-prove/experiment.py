"""Real public CLI workflow experiment; private fixture keys remain outside Git."""
import ast,sys,json,hashlib,argparse,subprocess,os
from pathlib import Path
ROOT=Path('/home/soultransit/devtony/ranex-acceptance-loop')
sys.path.insert(0,str(ROOT/'tests/integration'))
from test_acceptance_task_cli import invoke,git,PG
from test_http_observer_cli import setup,profile
from ranex.foundation.signing import generate_keypair
from ranex.foundation.specification_abc import canonical_payload_bytes
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
base=args.output.absolute();base.mkdir()
def require(condition,detail):
 if not condition:raise RuntimeError(detail)
p=profile();p['repetitions']=1;p['controls'][0]['fails']='tenant-isolation'
def request(id,method,role,body,expect):return dict(id=id,request=dict(method=method,path='/orders',role=role,body=body),expect=[dict(path=path,equals=value) for path,value in expect],capture={})
p['steps'] += [request('create','POST','alice',{'item':'real order'},[(['status'],201)]),request('tenant-isolation','GET','bob',None,[(['status'],200),(['json'],[])])]
root,_,_=setup(base,p)
module=ast.parse((ROOT/'tests/integration/test_http_observer_cli.py').read_text())
schema=next(n.value.value for n in ast.walk(module) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='schema' for t in n.targets))
bad=schema.replace('USING(owner=current_user)','USING(true)')
boundary="if printf tamper > acceptance/http.json; then exit 91; fi\nif printf escape > escape.txt; then exit 92; fi\nif ln acceptance/http.json product/hardlink; then exit 93; fi\n"
worker=dict(version='docker-worker-v1',image=PG,argv=['/bin/sh','-c',boundary+"cat > product/schema.sql <<'SQL'\n"+bad+'SQL\n'],product_roots=['product'],timeout_seconds=30,network=False,environment=[])
(root/'acceptance/worker.json').write_bytes(canonical_payload_bytes(worker));git(root,'add','.');git(root,'commit','-qm','freeze live task')
frozen=base/'task-bundle'
r=invoke('specification','freeze-probes','--external-repository',root,'--spec-packet',base/'A.json','--invocation',base/'argv.json','--root','acceptance','--output',frozen);require(r.returncode==0,r.stderr)
pin=json.loads(r.stdout)['manifest_digest'];private,_=generate_keypair();key=base/'owner.key';key.write_text(private);key.chmod(0o600);state=base/'state'
steps=[('approve',['specification','approve-task','--external-repository',root,'--bundle',frozen,'--manifest-digest',pin,'--worker-profile','acceptance/worker.json','--state',state]),('build',['specification','build-task','--task',state])]
for name,args in steps:
 r=invoke(*args,key=key if name=='approve' else None);require(r.returncode==0,r.stderr)
 (base/(name+'.json')).write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as pool:
 results=list(pool.map(lambda i:invoke('prove','--task',state),range(4)))
for i,r in enumerate(results):
 (base/('parallel-'+str(i)+'.json')).write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
misses=sorted(json.loads(r.stdout)['misses'] for r in results if r.returncode==1)
require(misses==[1,2,3] and sum(r.returncode==2 and 'E-TASK-REVOKED' in r.stderr for r in results)==1,'concurrent attempts escaped miss budget')
print(json.dumps({'parallel_misses':misses,'revoked':1}),flush=True)

packet=json.loads((base/'A.json').read_bytes());packet['revision']+=1
(base/'A2.json').write_bytes(canonical_payload_bytes(packet))
worker['argv'][-1]="cat > product/schema.sql <<'SQL'\n"+schema+'SQL\n'
(root/'acceptance/worker.json').write_bytes(canonical_payload_bytes(worker));git(root,'commit','-qam','operator approves corrected worker and newer map')
bundle2=base/'bundle2'
r=invoke('specification','freeze-probes','--external-repository',root,'--spec-packet',base/'A2.json','--invocation',base/'argv.json','--root','acceptance','--output',bundle2);require(r.returncode==0,r.stderr)
pin2=json.loads(r.stdout)['manifest_digest']
for name,args in [('reapprove',['specification','reapprove-task','--external-repository',root,'--bundle',bundle2,'--manifest-digest',pin2,'--worker-profile','acceptance/worker.json','--task',state]),('rebuild',['specification','build-task','--task',state]),('reprove',['prove','--task',state]),('land',['specification','land-task','--task',state]),('land-again',['specification','land-task','--task',state])]:
 if name=='land':
  # Actual target/candidate/receipt changes must refuse integration. Restore
  # only this experiment's disposable fixtures between independent controls.
  candidate_root=state/'candidate';old=git(candidate_root,'rev-parse','HEAD')
  (candidate_root/'product/stale.txt').write_text('unobserved change\n');git(candidate_root,'add','.');git(candidate_root,'-c','user.name=Experiment','-c','user.email=experiment@ranex.invalid','commit','-qm','unobserved candidate')
  rejected=invoke('specification','land-task','--task',state)
  (base/'stale-candidate.json').write_text(json.dumps({'exit':rejected.returncode,'stderr':rejected.stderr}))
  require(rejected.returncode==2 and 'E-TASK-PASS' in rejected.stderr,'stale candidate accepted')
  git(candidate_root,'reset','--hard',old)
  original=git(root,'rev-parse','HEAD');(root/'moved.txt').write_text('parallel target change\n');git(root,'add','.');git(root,'commit','-qm','target advanced')
  rejected=invoke('specification','land-task','--task',state)
  (base/'moved-target.json').write_text(json.dumps({'exit':rejected.returncode,'stderr':rejected.stderr}))
  require(rejected.returncode==2 and 'E-TASK-TARGET-MOVED' in rejected.stderr,'moved target accepted')
  git(root,'reset','--hard',original)
 r=invoke(*args,key=key if name=='reapprove' else None);(base/(name+'.json')).write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));print(name,r.returncode,r.stdout,r.stderr,flush=True)
 require(r.returncode==(2 if name=='land-again' else 0),name+': '+r.stderr)
 if name=='reprove':
  passed=json.loads(r.stdout);require(passed['status']=='PASS' and passed['misses']==0,'new approval did not pass')
 if name=='land-again':require('E-TASK-LANDED' in r.stderr,'duplicate integration accepted')

require(git(root,'rev-parse','HEAD')==passed['candidate'],'integrated a different commit')
require(not git(root,'status','--porcelain'),'integration checkout dirty')
require((root/'product/schema.sql').read_text()==schema,'delivered SQL differs')
context=json.loads((state/'context.json').read_bytes())
require(len(list(state.glob('observation-*')))==4,'fourth miss attempt started a process')
summary={'status':'EXPERIMENT-MATCH','candidate':passed['candidate'],'misses':[1,2,3],'fourth_attempt':'REFUSED','reapproved_misses':0,'integrated_tree':git(root,'rev-parse','HEAD^{tree}'),'product_sha256':hashlib.sha256((root/'product/schema.sql').read_bytes()).hexdigest(),'controller_sha256':hashlib.sha256((ROOT/'src/ranex/cli/acceptance_task.py').read_bytes()).hexdigest(),'worker':'deterministic SQL-writing fixture, not a qualified AI harness'}
(base/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
