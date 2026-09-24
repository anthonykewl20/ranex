"""Public observer CLI; the opt-in journey uses real Docker/PostgreSQL/HTTP."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import canonical_payload_bytes

REPO = Path(__file__).resolve().parents[2]
PG = 'sha256:e013e867e712fec275706a6c51c966f0bb0c93cfa8f51000f85a15f9865a28cb'
API = 'sha256:5922bde07147b82b1c9d8f749e48c1e5b99ebb233f3888bb7ab65f07cf4ac82d'


def cli(*args):
    return subprocess.run([sys.executable, '-m', 'ranex.cli.main', 'specification', *map(str,args)],
        cwd=REPO, env={**os.environ,'PYTHONPATH':str(REPO/'src')}, capture_output=True,text=True,timeout=180,check=False)


def git(root,*args):
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,check=False)
    assert p.returncode==0,p.stderr
    return p.stdout.strip()


def setup(tmp_path, profile):
    root=tmp_path/'subject';root.mkdir();git(root,'init','-q')
    git(root,'config','user.email','observer@example.invalid');git(root,'config','user.name','Observer')
    (root/'acceptance').mkdir();(root/'product').mkdir()
    (root/'acceptance/http.json').write_bytes(canonical_payload_bytes(profile))
    (root/'product/schema.sql').write_text('SELECT 1;\n')
    git(root,'add','.');git(root,'commit','-qm','frozen observer')
    vectors=json.loads((REPO/'tests/contract/fixtures/specification/abc-v1-vectors.json').read_bytes())
    packet=tmp_path/'A.json';packet.write_bytes(canonical_payload_bytes(vectors['triple']['a']))
    argv=tmp_path/'argv.json';argv.write_bytes(canonical_payload_bytes(['ranex','specification','observe-http','--profile','acceptance/http.json']))
    bundle=tmp_path/'bundle'
    p=cli('freeze-probes','--external-repository',root,'--spec-packet',packet,'--invocation',argv,'--root','acceptance','--output',bundle)
    assert p.returncode==0,p.stderr
    return root,bundle,json.loads(p.stdout)['manifest_digest']


def profile():
    return dict(version='postgrest-http-v1',observer_digest='sha256:'+hashlib.sha256((REPO/'src/ranex/cli/http_observer.py').read_bytes()).hexdigest(),postgres_image=PG,api_image=API,schema='product/schema.sql',timeout_seconds=20,max_body_bytes=65536,repetitions=3,controls=[dict(id='remove-isolation',old='USING(owner=current_user)',new='USING(true)',fails='invalid-token')],
        steps=[dict(id='invalid-token',request=dict(method='GET',path='/orders',role='invalid',body=None),expect=[dict(path=['status'],equals=401)],capture={})])


@pytest.mark.parametrize('change', ['empty','mutable-image','path-escape','mock-field','no-expectation','duplicate-id','no-controls','unknown-control-assertion','no-repetitions','wrong-observer'])
def test_observer_refuses_invalid_frozen_contract_before_launch(tmp_path,change):
    p=profile()
    if change=='empty':p['steps']=[]
    elif change=='mutable-image':p['api_image']='postgrest:latest'
    elif change=='path-escape':p['schema']='../schema.sql'
    elif change=='mock-field':p['mock_transport']=True
    elif change=='no-expectation':p['steps'][0]['expect']=[]
    elif change=='duplicate-id':p['steps']*=2
    elif change=='no-controls':p['controls']=[]
    elif change=='unknown-control-assertion':p['controls'][0]['fails']='absent'
    elif change=='no-repetitions':p['repetitions']=0
    else:p['observer_digest']='sha256:'+'0'*64
    root,bundle,pin=setup(tmp_path,p)
    out=tmp_path/'observations'
    result=cli('observe-http','--external-repository',root,'--bundle',bundle,'--manifest-digest',pin,'--profile','acceptance/http.json','--output',out)
    assert result.returncode==2
    assert 'E-HTTP-CONTRACT' in result.stderr
    assert not out.exists()


def test_observer_requires_frozen_command_identity(tmp_path):
    root,bundle,pin=setup(tmp_path,profile())
    result=cli('observe-http','--external-repository',root,'--bundle',bundle,'--manifest-digest','sha256:'+'0'*64,'--profile','acceptance/http.json','--output',tmp_path/'out')
    assert result.returncode==2
    assert 'E-PROBE-PIN' in result.stderr
    assert not (tmp_path/'out').exists()
    comma=cli('observe-http','--external-repository',root,'--bundle',bundle,'--manifest-digest',pin,'--profile','acceptance/http.json','--output',tmp_path/'has,comma')
    assert comma.returncode==2
    assert 'E-HTTP-CONTRACT' in comma.stderr
    assert not (tmp_path/'has,comma').exists()


@pytest.mark.skipif(os.environ.get('RANEX_LIVE_HTTP_EXPERIMENT') != '1', reason='ranex-context:live-http-experiment: requires RANEX_LIVE_HTTP_EXPERIMENT=1 and local Docker images')
def test_real_http_observer_matches_good_and_rejects_committed_authorization_defect(tmp_path):
    p=profile()
    def request(id,method,path,role,body,expect,capture=None):
        return dict(id=id,request=dict(method=method,path=path,role=role,body=body),expect=[dict(path=path,equals=value) for path,value in expect],capture=capture or {})
    p['steps'] += [
        request('invalid-order','POST','/orders','alice',{'item':None},[(['status'],400)]),
        request('create-order','POST','/orders','alice',{'item':'acceptance order'},[(['status'],201),(['json',0,'owner'],'alice'),(['json',0,'item'],'acceptance order')],{'order_id':['json',0,'id']}),
        request('owner-read','GET','/orders?id=eq.{order_id}','alice',None,[(['status'],200),(['json'],[{'id':{'var':'order_id'},'owner':'alice','item':'acceptance order'}])]),
        request('tenant-isolation','GET','/orders?id=eq.{order_id}','bob',None,[(['status'],200),(['json'],[])]),
        request('forged-owner','POST','/orders','bob',{'owner':'alice','item':'forged'},[(['status'],403)]),
        dict(id='restart-application',control='restart-app'),
        request('application-persistence','GET','/orders?id=eq.{order_id}','alice',None,[(['status'],200),(['json',0,'id'],{'var':'order_id'})]),
        dict(id='stop-database',control='stop-db'),
        request('dependency-unavailable','GET','/orders','alice',None,[(['status'],503)]),
        dict(id='start-database',control='start-db'),
        request('database-persistence','GET','/orders?id=eq.{order_id}','alice',None,[(['status'],200),(['json',0,'id'],{'var':'order_id'})]),
    ]
    p['controls'][0]['fails']='tenant-isolation'
    root,bundle,pin=setup(tmp_path,p)
    schema='''CREATE ROLE authenticator LOGIN NOINHERIT PASSWORD 'experiment-api';
CREATE ROLE alice NOLOGIN; CREATE ROLE bob NOLOGIN; CREATE ROLE anon NOLOGIN;
GRANT alice,bob,anon TO authenticator;
CREATE SCHEMA api; GRANT USAGE ON SCHEMA api TO alice,bob,anon;
CREATE TABLE api.orders(id serial PRIMARY KEY,owner name NOT NULL DEFAULT current_user,item text NOT NULL);
ALTER TABLE api.orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY isolation ON api.orders USING(owner=current_user) WITH CHECK(owner=current_user);
GRANT SELECT,INSERT ON api.orders TO alice,bob;
GRANT USAGE ON SEQUENCE api.orders_id_seq TO alice,bob;
'''
    (root/'product/schema.sql').write_text(schema);git(root,'commit','-qam','working product after freeze')
    good=cli('observe-http','--external-repository',root,'--bundle',bundle,'--manifest-digest',pin,'--profile','acceptance/http.json','--output',tmp_path/'good')
    assert good.returncode==0,good.stdout+good.stderr
    receipt=json.loads(good.stdout)
    assert receipt['status']=='OBSERVED-MATCH'
    assert receipt['candidate_commit']==git(root,'rev-parse','HEAD')
    assert receipt['identities'] and not receipt['cleanup_errors']
    assert receipt['calibrated'] is True
    assert len(receipt['trials'])==6
    assert all(t['failed_assertion']=='tenant-isolation' for t in receipt['trials'] if t['control'] is not None)
    assert receipt['observations'][-1]['status']==200
    (root/'product/schema.sql').write_text(schema.replace('USING(owner=current_user)','USING(true)'))
    git(root,'commit','-qam','known-bad product isolation defect')
    bad=cli('observe-http','--external-repository',root,'--bundle',bundle,'--manifest-digest',pin,'--profile','acceptance/http.json','--output',tmp_path/'bad')
    assert bad.returncode==1,bad.stdout+bad.stderr
    receipt=json.loads(bad.stdout)
    assert receipt['status']=='OBSERVED-MISMATCH'
    assert receipt['failed_assertion']=='tenant-isolation'
    assert receipt['candidate_commit']==git(root,'rev-parse','HEAD')
    assert not receipt['cleanup_errors']
    assert json.loads(receipt['observations'][-1]['body'])[0]['owner']=='alice'
    # These controls must block calibration, even when the baseline is good.
    # Keep each revised contract in a separately frozen bundle.
    import copy
    for label,replacement,expected_step,trial_status in (
        ('surviving-control','USING((owner=current_user))','tenant-isolation','OBSERVED-MATCH'),
        ('compile-error','USING(','tenant-isolation','OBSERVATION-ERROR'),
        ('wrong-assertion','USING(true)','invalid-token','OBSERVED-MISMATCH'),
    ):
        directory=tmp_path/label;directory.mkdir()
        revised=copy.deepcopy(p);revised['repetitions']=1
        revised['controls'][0].update(new=replacement,fails=expected_step)
        candidate,frozen,digest=setup(directory,revised)
        (candidate/'product/schema.sql').write_text(schema)
        git(candidate,'commit','-qam','working product')
        result=cli('observe-http','--external-repository',candidate,'--bundle',frozen,'--manifest-digest',digest,'--profile','acceptance/http.json','--output',directory/'out')
        assert result.returncode==2,result.stdout+result.stderr
        refused=json.loads(result.stdout)
        assert refused['status']=='CALIBRATION-FAILED'
        assert refused['calibrated'] is False
        assert refused['trials'][0]['status']=='OBSERVED-MATCH'
        assert refused['trials'][1]['status']==trial_status
        assert refused['failed_control']=='remove-isolation'
