"""Trusted declarative HTTP observer for a pinned PostgREST/PostgreSQL profile.

This records calibrated observations, not approval, a product PASS or a merge.
Docker and the controller are trusted. Candidate SQL runs only in the database
container; candidate Python, scripts and claimed test reports are never loaded.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

from ranex.cli.probe_bundle import _path, _regular_read, check_bundle
from ranex.cli.repository import committable_into, git
from ranex.cli.subject import SubjectError, materialise_subject
from ranex.foundation.specification_abc import canonical_payload_bytes, parse_canonical_payload

_DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
_NAME = re.compile(r'[a-zA-Z][a-zA-Z0-9_-]{0,63}\Z')
_SECRET = 'ranex-local-observer-public-test-secret-0123456789'


def require(condition, detail):
    if not condition:
        raise ValueError('E-HTTP-CONTRACT: ' + detail)


def validate_profile(value):
    require(isinstance(value, dict) and set(value) == {'version','postgres_image','api_image','schema','timeout_seconds','max_body_bytes','steps','controls','repetitions','observer_digest'}, 'closed profile fields required')
    require(value['version'] == 'postgrest-http-v1', 'unknown profile version')
    for name in ('postgres_image', 'api_image', 'observer_digest'):
        require(isinstance(value[name], str) and _DIGEST.fullmatch(value[name]), 'local immutable image IDs required')
    try:
        _path(value['schema'])
    except ValueError:
        require(False, 'schema must be a portable candidate path')
    require(type(value['timeout_seconds']) is int and 1 <= value['timeout_seconds'] <= 60, 'deadline must be 1..60 seconds')
    require(type(value['max_body_bytes']) is int and 1 <= value['max_body_bytes'] <= 1048576, 'body bound must be 1..1048576 bytes')
    steps = value['steps']
    require(isinstance(steps, list) and 1 <= len(steps) <= 100, '1..100 steps required')
    ids = set(); variables = set(); requests = 0
    def selector(path):
        require(isinstance(path, list) and len(path) <= 20 and all(isinstance(p,str) or type(p) is int and p >= 0 for p in path), 'invalid response selector')
    def references(item):
        if isinstance(item, dict):
            if set(item) == {'var'}:
                require(isinstance(item['var'],str) and item['var'] in variables, 'variable must have been captured by an earlier request')
            else:
                for nested in item.values(): references(nested)
        elif isinstance(item, list):
            for nested in item: references(nested)
    for step in steps:
        require(isinstance(step,dict) and isinstance(step.get('id'),str) and _NAME.fullmatch(step['id']) and step['id'] not in ids, 'unique step IDs required')
        ids.add(step['id'])
        if 'control' in step:
            require(set(step)=={'id','control'} and step['control'] in ('restart-app','stop-db','start-db'), 'unknown process control')
            continue
        requests += 1
        require(set(step)=={'id','request','expect','capture'}, 'closed HTTP step required')
        request = step['request']
        require(isinstance(request,dict) and set(request)=={'method','path','role','body'}, 'closed HTTP request required')
        require(request['method'] in ('GET','POST','PATCH','DELETE'), 'unsupported method')
        require(isinstance(request['path'],str) and request['path'].startswith('/') and not request['path'].startswith('//') and len(request['path']) <= 4096 and not any(ord(c)<32 or ord(c)>126 for c in request['path']), 'local ASCII HTTP path required')
        require(request['role'] in (None,'alice','bob','invalid'), 'unsupported test role')
        references(request['body'])
        require(isinstance(step['expect'],list) and step['expect'], 'every HTTP request requires observations to assert')
        for assertion in step['expect']:
            require(isinstance(assertion,dict) and set(assertion)=={'path','equals'}, 'closed equality assertion required')
            selector(assertion['path']);references(assertion['equals'])
        captures = step['capture']
        require(isinstance(captures,dict), 'capture mapping required')
        for name,path in captures.items():
            require(_NAME.fullmatch(name) and name not in variables, 'capture names must be unique')
            selector(path)
        # Validate format syntax before containers are started. Only prior simple
        # scalar names may appear; attribute/index traversal is not supported.
        import string
        try:
            for _,name,format_spec,conversion in string.Formatter().parse(request['path']):
                require(name is None or name in variables and not format_spec and not conversion, 'invalid URL variable')
        except ValueError as exc:
            require(False, str(exc))
        variables.update(captures)
    require(requests > 0, 'at least one HTTP assertion required')
    require(type(value['repetitions']) is int and 1 <= value['repetitions'] <= 5, '1..5 frozen repetitions required')
    controls=value['controls']
    require(isinstance(controls,list) and 1 <= len(controls) <= 10, '1..10 known-bad controls required')
    control_ids=set()
    for control in controls:
        require(isinstance(control,dict) and set(control)=={'id','old','new','fails'}, 'closed product mutation required')
        require(isinstance(control['id'],str) and _NAME.fullmatch(control['id']) and control['id'] not in control_ids, 'unique control IDs required')
        control_ids.add(control['id'])
        require(all(isinstance(control[name],str) and 1 <= len(control[name]) <= 65536 for name in ('old','new')) and control['old'] != control['new'], 'nonempty distinct bounded mutation bytes required')
        require(control['fails'] in [step['id'] for step in steps if 'request' in step], 'control must name an HTTP assertion')
    return value


def select(value, path):
    for part in path:
        if type(part) is int:
            if not isinstance(value,list): raise KeyError(part)
        elif not isinstance(value,dict): raise KeyError(part)
        value = value[part]
    return value


def expand(value, variables):
    if isinstance(value,dict):
        if set(value)=={'var'}: return variables[value['var']]
        return {key:expand(item,variables) for key,item in value.items()}
    if isinstance(value,list): return [expand(item,variables) for item in value]
    return value


class Observer:
    def __init__(self, profile, output, home):
        self.profile = profile; self.output = output
        self.commands = []; self.observations = []; self.identities = []; self.resources = []
        self.env = {'PATH':'/usr/bin:/bin','HOME':str(home),'LC_ALL':'C','DOCKER_HOST':'unix:///var/run/docker.sock'}
        prefix = 'ranex-observe-' + uuid.uuid4().hex
        self.db = prefix+'-db'; self.app=prefix+'-api'; self.network=prefix+'-net'; self.volume=prefix+'-data'
        self.host = None

    def docker(self,*args,input=None,required=True):
        argv=['/usr/bin/docker',*args]
        try:
            p=subprocess.run(argv,input=input,capture_output=True,text=True,env=self.env,timeout=self.profile['timeout_seconds'])
        except subprocess.TimeoutExpired:
            self.commands.append({'argv':argv,'timeout':True})
            raise RuntimeError('Docker command deadline exceeded')
        self.commands.append(dict(argv=argv,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,
            stdin_sha256=None if input is None else hashlib.sha256(input.encode()).hexdigest()))
        if required and p.returncode: raise RuntimeError(p.stderr or 'Docker command failed')
        return p.stdout.strip(),p.returncode

    def identity(self,name,image):
        data=json.loads(self.docker('inspect',name)[0])[0]
        if data['Image'] != image or not data['State']['Running']:
            raise RuntimeError('wrong image or stopped container')
        self.identities.append({key:data[key] for key in ('Id','Image','State','NetworkSettings')})
        return data

    def start(self, schema):
        for name in ('postgres_image','api_image'):
            observed=json.loads(self.docker('image','inspect',self.profile[name])[0])[0]
            if observed['Id'] != self.profile[name]: raise RuntimeError('image identity mismatch')
        self.docker('network','create','--internal',self.network);self.resources.append(('network',self.network))
        self.docker('volume','create',self.volume);self.resources.append(('volume',self.volume))
        # Register names before run: a timed-out create/run can still have created
        # its container, which must be included in cleanup.
        self.resources.append(('container',self.db))
        self.docker('run','--pull=never','-d','--name',self.db,'--network',self.network,'--network-alias','database',
            '--memory','256m','--pids-limit','128','--security-opt','no-new-privileges',
            '-e','POSTGRES_PASSWORD=ranex-observer-test','--mount','type=volume,source='+self.volume+',target=/var/lib/postgresql/data',self.profile['postgres_image'])
        deadline=time.monotonic()+self.profile['timeout_seconds']
        while True:
            _,code=self.docker('exec',self.db,'pg_isready','-h','127.0.0.1','-U','postgres',required=False)
            if code==0: break
            if time.monotonic()>=deadline: raise RuntimeError('database readiness deadline exceeded')
            time.sleep(.1)
        self.identity(self.db,self.profile['postgres_image'])
        self.docker('exec','-i','-e','PGOPTIONS=-c statement_timeout=15000',self.db,'psql','-q','-o','/dev/null','-U','postgres','-v','ON_ERROR_STOP=1',input=schema)
        config='db-uri = "postgresql://authenticator:experiment-api@database:5432/postgres"\ndb-schemas = "api"\ndb-anon-role = "anon"\njwt-secret = "'+_SECRET+'"\nserver-host = "0.0.0.0"\nserver-port = 3000\ndb-pool-acquisition-timeout = 1\n'
        config_path=self.output/'postgrest.conf';config_path.write_text(config);config_path.chmod(0o644)
        self.resources.append(('container',self.app))
        self.docker('run','--pull=never','-d','--name',self.app,'--network',self.network,'--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--pids-limit','64','--memory','128m',
            '--mount','type=bind,source='+str(config_path)+',target=/config,readonly',self.profile['api_image'],'/bin/postgrest','/config')
        identity=self.identity(self.app,self.profile['api_image'])
        self.host=identity['NetworkSettings']['Networks'][self.network]['IPAddress']
        if not self.host: raise RuntimeError('missing controller-owned endpoint')
        self.ready()

    def request(self,id,method,path,role,body):
        headers={}
        if role:
            def enc(value): return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).rstrip(b'=')
            token=enc({'alg':'HS256','typ':'JWT'})+b'.'+enc({'role':role})
            token=(token+b'.'+base64.urlsafe_b64encode(hmac.digest(_SECRET.encode(),token,'sha256')).rstrip(b'=')).decode()
            headers['Authorization']='Bearer '+('invalid' if role=='invalid' else token)
        if body is not None: headers.update({'Content-Type':'application/json','Prefer':'return=representation'})
        connection=http.client.HTTPConnection(self.host,3000,timeout=min(5,self.profile['timeout_seconds']))
        try:
            connection.request(method,path,None if body is None else json.dumps(body),headers)
            response=connection.getresponse(); raw=response.read(self.profile['max_body_bytes']+1)
            if len(raw)>self.profile['max_body_bytes']: raise RuntimeError('HTTP body exceeds frozen bound')
            text=raw.decode('utf-8')
            row=dict(id=id,method=method,path=path,role=role,request_body=body,status=response.status,body=text)
            self.observations.append(row)
            return dict(status=response.status,json=json.loads(text) if text else None)
        finally: connection.close()

    def ready(self):
        deadline=time.monotonic()+self.profile['timeout_seconds']
        while True:
            try:
                if self.request('controller-readiness','GET','/','alice',None)['status']==200: return
            except (OSError,http.client.HTTPException): pass
            if time.monotonic()>=deadline: raise RuntimeError('HTTP readiness deadline exceeded')
            time.sleep(.1)

    def run(self):
        from urllib.parse import quote
        variables={}
        for step in self.profile['steps']:
            if 'control' in step:
                action=step['control']
                target=self.app if action=='restart-app' else self.db
                self.docker('restart' if action=='restart-app' else 'stop' if action=='stop-db' else 'start',target)
                if action!='stop-db':
                    identity=self.identity(target,self.profile['api_image' if target==self.app else 'postgres_image'])
                    if target==self.app:
                        self.host=identity['NetworkSettings']['Networks'][self.network]['IPAddress']
                    self.ready()
                self.observations.append(dict(id=step['id'],control=action,completed=True))
                continue
            req=step['request']
            path=req['path'].format_map({key:quote(str(value),safe='') for key,value in variables.items()})
            response=self.request(step['id'],req['method'],path,req['role'],expand(req['body'],variables))
            for assertion in step['expect']:
                try: actual=select(response,assertion['path'])
                except (KeyError,IndexError,TypeError): return step['id']
                expected=expand(assertion['equals'],variables)
                # Canonical comparison distinguishes booleans from integers.
                if canonical_payload_bytes(actual)!=canonical_payload_bytes(expected): return step['id']
            for name,path in step['capture'].items():
                try: value=select(response,path)
                except (KeyError,IndexError,TypeError): return step['id']
                if type(value) not in (str,int): return step['id']
                variables[name]=value
        return None

    def cleanup(self):
        errors=[]
        for kind,name in reversed(self.resources):
            try:
                if kind=='container':
                    self.docker('logs','--tail','100',name,required=False)
                    _,code=self.docker('rm','-f',name,required=False)
                else: _,code=self.docker(kind,'rm',name,required=False)
                if code: errors.append(name)
            except (OSError,RuntimeError): errors.append(name)
        return errors


def observe(root,bundle,pin,relative,output):
    checked=check_bundle(root,bundle,pin)
    descriptor=parse_canonical_payload(_regular_read(bundle,'probe-contract.json'))
    require(relative in {row['path'] for row in descriptor['entries']}, 'profile must be frozen in the bundle')
    require(descriptor['argv']==['ranex','specification','observe-http','--profile',relative], 'frozen invocation differs from observer command')
    profile=validate_profile(parse_canonical_payload(_regular_read(bundle,'probes/'+_path(relative))))
    require(profile['observer_digest']=='sha256:'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'observer implementation differs from frozen profile')
    output=output.absolute()
    require(',' not in str(output) and output==output.resolve() and not committable_into(output,root), 'output must be external without symlinks')
    with materialise_subject(root,checked['candidate_commit'],git) as candidate:
        schema=_regular_read(candidate.tree,profile['schema'])
        require(len(schema)<=1048576, 'schema exceeds 1 MiB bound')
        schema=schema.decode('utf-8')
        output.mkdir(mode=0o700)
        trials=[]
        def run_trial(schema_text, repeat, control):
            directory=output/('baseline-'+str(repeat) if control is None else control['id']+'-'+str(repeat))
            directory.mkdir()
            observer=Observer(profile,directory,candidate.home)
            status='OBSERVATION-ERROR';failure=None;error=None
            try:
                observer.start(schema_text);failure=observer.run()
                status='OBSERVED-MISMATCH' if failure else 'OBSERVED-MATCH'
            except (OSError,ValueError,RuntimeError,http.client.HTTPException) as exc:
                error=str(exc)
            finally:
                cleanup_errors=observer.cleanup()
                if cleanup_errors: status='OBSERVATION-ERROR'
                trial=dict(status=status,failed_assertion=failure,error=error,cleanup_errors=cleanup_errors,
                    repeat=repeat,control=None if control is None else control['id'],
                    schema_sha256=hashlib.sha256(schema_text.encode()).hexdigest(),
                    identities=observer.identities,observations=observer.observations)
                (directory/'commands.json').write_bytes(canonical_payload_bytes(observer.commands))
                (directory/'receipt.json').write_bytes(canonical_payload_bytes(trial))
            trials.append(trial)
            return trial
        baseline=None;failed_control=None;status='OBSERVATION-ERROR';error=None
        for repeat in range(profile['repetitions']):
            baseline=run_trial(schema,repeat,None)
            status=baseline['status']
            if status!='OBSERVED-MATCH': break
            for control in profile['controls']:
                if schema.count(control['old'])!=1:
                    failed_control=control['id'];status='CALIBRATION-FAILED';error='mutation target must occur exactly once';break
                trial=run_trial(schema.replace(control['old'],control['new']),repeat,control)
                if trial['status']!='OBSERVED-MISMATCH' or trial['failed_assertion']!=control['fails']:
                    failed_control=control['id'];status='CALIBRATION-FAILED';error='control did not fail its named assertion';break
            if failed_control: break
        record=dict(version='http-observation-v1',status=status,calibrated=status=='OBSERVED-MATCH',
            failed_assertion=baseline['failed_assertion'],failed_control=failed_control,error=error or baseline['error'],
            cleanup_errors=[item for trial in trials for item in trial['cleanup_errors']],
            candidate_commit=checked['candidate_commit'],manifest_digest=pin,
            command_digest=checked['command_digest'],schema_sha256=hashlib.sha256(schema.encode()).hexdigest(),
            observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            identities=baseline['identities'],observations=baseline['observations'],trials=trials,
            limitations=['Trusted Linux controller and Docker daemon','PostgREST SQL profile only','Not approval, verdict admission or merge'])
        (output/'receipt.json').write_bytes(canonical_payload_bytes(record))
        return record


def cmd_observe(args):
    from ranex.cli.main import _command_repository
    try:
        record=observe(_command_repository(args),Path(args.bundle),args.manifest_digest,args.profile,Path(args.output))
    except (OSError,ValueError,SubjectError) as exc:
        print(str(exc),file=sys.stderr);return 2
    print(canonical_payload_bytes(record).decode())
    return 0 if record['status']=='OBSERVED-MATCH' else 1 if record['status']=='OBSERVED-MISMATCH' else 2


def register(commands):
    parser=commands.add_parser('observe-http',help='observe a frozen PostgREST HTTP journey; not a product verdict')
    for name in ('bundle','manifest-digest','profile','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--external-repository')
    parser.set_defaults(func=cmd_observe)
