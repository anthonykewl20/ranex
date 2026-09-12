import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

scratch=Path(sys.argv[1]).resolve()
scratch.mkdir(parents=True, exist_ok=True)
repository=scratch/'freeze-subject'
home=scratch/'freeze-home'
home.mkdir()
subprocess.run(['git','clone','--quiet',str(Path.cwd()),str(repository)],check=True)
env={k:v for k,v in os.environ.items() if k not in ('RANEX_SIGNING_KEY','RANEX_VERDICT_SIGNING_KEY','RANEX_VERDICT_DIR','COVERAGE_PROCESS_START','COVERAGE_PROCESS_CONFIG','COVERAGE_FILE','RANEX_TRACE','RANEX_TRACE_EVENT','RANEX_TRACE_PARENT_SID')}
env['HOME']=str(home)
env['PYTHONPATH']=str(repository/'src')
env.setdefault('LC_ALL','C')
env.setdefault('TZ','UTC')
records=[]
def run(name,arguments,timeout):
 argv=[sys.executable,'-m','ranex.cli.main',*arguments]
 start=time.time()
 with (scratch/f'{name}.stdout').open('wb') as out,(scratch/f'{name}.stderr').open('wb') as err:
  result=subprocess.run(argv,cwd=repository,env=env,stdout=out,stderr=err,timeout=timeout,check=False)
 records.append({'argv':argv,'cwd':str(repository),'started':start,'elapsed_seconds':time.time()-start,'exit_code':result.returncode})
 (scratch/'freeze-receipt.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,'exit',result.returncode,flush=True)
 if result.returncode:
  print((scratch/f'{name}.stdout').read_text()[-5000:])
  print((scratch/f'{name}.stderr').read_text()[-5000:])
  raise SystemExit(result.returncode)
run('deps-fetch',['deps','fetch','--repository','.'],600)
run('deps-approve',['deps','approve','--repository','.','--approver','leitir-lane-experiment'],120)
manifest=json.loads((repository/'governance/suite_manifest.json').read_bytes())
argv=['suite','freeze','--artifact','governance/suite_results.xml','--output','.local/leitir-lane-manifest.json']
for test,reason in manifest['expected_skips'].items():
 argv.extend(['--expected-skip',f'{test}={reason}'])
argv.extend(['--','uv','run','pytest','-q','-o','xfail_strict=true','-p','ranex.foundation.pytest_xpass','--junitxml=governance/suite_results.xml'])
run('freeze',argv,1800)
sys.path.insert(0,str(repository/'src'))
from ranex.foundation.suite_results import load_manifest
produced=repository/'.local/leitir-lane-manifest.json'
loaded=load_manifest(produced)
shutil.copyfile(produced,scratch/'suite_manifest.json')
print('load_manifest: VALID',len(loaded['suite']),'tests',len(loaded['expected_skips']),'expected skips',flush=True)
print('manifest sha256',hashlib.sha256(produced.read_bytes()).hexdigest(),flush=True)
