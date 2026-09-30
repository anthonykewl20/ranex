"""Durable approved acceptance tasks, composed from the existing kernel.

The controller directory and Docker daemon are trusted. Workers only receive
an isolated candidate plus explicitly writable product roots; they never own
approval keys, the journal, observation outcomes or the publication key.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from ranex.cli.http_observer import observe, validate_profile
from ranex.cli.probe_bundle import _path, _regular_read, _roots, _selected, check_bundle
from ranex.cli.repository import committable_into, git, uncommitted_paths
from ranex.cli.subject import SubjectError, materialise_subject
from ranex.foundation import atomic_writer
from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.signing import generate_keypair, public_key_for
from ranex.foundation.specification_abc import (
    assert_abc_chain,
    canonical_payload_bytes,
    parse_canonical_payload,
    payload_digest,
    sign_approval_payload,
)
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, verify_verdict
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.application.specification_approval import issue_approval
from ranex.governed_execution.domain.specification_approval import (
    ApprovalPendingContext,
    CapabilityGrant,
    PolicyCapabilities,
    RoleAssignment,
    RoleAssignments,
)
from ranex.governed_execution.domain.specification_events import (
    SpecificationEvent,
    approval_revoked_event,
    evaluate_use,
    grant_revoked_event,
)
from ranex.governed_execution.domain.verdict import Claim, Evidence, Gate, evaluate
from ranex.governed_execution.verdict_publication import publish_verdict

_DIGEST=re.compile(r'sha256:[0-9a-f]{64}\Z')
_ENV=re.compile(r'[A-Z_][A-Z0-9_]*\Z')


def refuse(detail): raise ValueError('E-TASK-'+detail)

def require(condition,detail):
    if not condition: refuse(detail)

def read(path): return parse_canonical_payload(Path(path).read_bytes())

def module_digest(): return 'sha256:'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def safe_git(root,*args,**kwargs):
    overrides=kwargs.pop('overrides',{})
    return git(root,'-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-c','commit.gpgsign=false',
        '-c','core.autocrlf=false','-c','core.eol=lf',*args,
        overrides={**overrides,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_ATTR_NOSYSTEM':'1'},**kwargs)

def checked_git(root,*args):
    result=safe_git(root,*args,timeout=60)
    require(result.returncode==0,'GIT: '+result.stderr.strip())
    return result.stdout.strip()


def worker_profile(value, frozen_roots):
    require(isinstance(value,dict) and set(value)=={'version','image','argv','product_roots','timeout_seconds','network','environment'},'WORKER: closed profile required')
    require(value['version']=='docker-worker-v1' and isinstance(value['image'],str) and _DIGEST.fullmatch(value['image']),'WORKER: immutable local image required')
    argv=value['argv']
    require(isinstance(argv,list) and argv and all(isinstance(a,str) and '\0' not in a for a in argv) and argv[0].startswith('/'),'WORKER: absolute entrypoint and literal argv required')
    require(type(value['timeout_seconds']) is int and 1<=value['timeout_seconds']<=1800,'WORKER: deadline must be 1..1800 seconds')
    require(type(value['network']) is bool,'WORKER: explicit network policy required')
    require(isinstance(value['environment'],list) and all(isinstance(n,str) and _ENV.fullmatch(n) for n in value['environment']) and len(set(value['environment']))==len(value['environment']),'WORKER: unique environment names required')
    roots=_roots(value['product_roots'])
    require(not any(_selected(root,frozen_roots) or _selected(frozen,[root]) for root in roots for frozen in frozen_roots),'SCOPE: product and frozen roots overlap')
    return value


@dataclass
class Record:
    value: dict
    def as_record(self): return self.value


def as_event(row):
    return SpecificationEvent(row['event_id'],row['kind'],row['journal_position']['seq'],row['journal_position']['head_link'],row['c_digest'],row['grant_id'],row['parent_grant_id'],row['principal_id'],row['key_id'],row['previous_event_digest'],row['code'])


class Task:
    def __init__(self,path):
        self.root=Path(path).absolute()
        require(self.root==self.root.resolve() and self.root.is_dir(),'ABSENT: task directory is missing or aliased')
        self.context=read(self.root/'context.json')
        self.c=self.context['c'];self.payload=self.c['payload'];self.c_digest=payload_digest(self.payload)
        assert_abc_chain(self.context['a'],self.context['b'],self.c)
        require(self.payload['key']==self.context['owner_key'],'OWNER: approval key changed')
        expected={'module':module_digest(),'worker':self.context['worker'],'identities':self.context['identities']}
        require(payload_digest(expected)==self.payload['profile_digests']['harness'],'DRIFT: task controller or worker profile changed')
        self.candidate=self.root/'candidate';self.journal=Journal(self.root/'journal.sqlite3')
        self.gate=Gate('live-acceptance','frozen-live-observations',(Claim('live-acceptance',self.context['command_digest']),),True)
        raw=read(self.root/'verdict.json');content={key:raw['record'][key] for key in SIGNED_FIELDS}
        signature=raw['signatures'][0]
        require(raw['payload_type']==PAYLOAD_TYPE and signature['signer_id']=='task-publisher' and verify_verdict(content,signature['signature'],self.context['identities']['publisher'],payload_type=raw['payload_type']),'ANCHOR: invalid publisher signature')
        require(raw['record']['record_digest']=='sha256:'+canonical_sha256(content),'ANCHOR: record digest mismatch')
        require(self.journal.verify(expected_head=content['journal_head']),'ANCHOR: journal changed or an interrupted append needs operator recovery')
        self.last_verdict=content
        grant=self.context['grant'];window=grant['time_window']
        self.grant=CapabilityGrant(grant['grant_id'],grant['c_digest'],grant['parent_grant_id'],PolicyCapabilities.from_record(grant['capabilities']),grant['worker_key'],grant['evaluator_key'],grant.get('publisher_key'),window['not_before'],window['not_after'])
        require(self.grant.c_digest==self.c_digest,'GRANT: wrong approval')

    def entries(self): return self.journal.entries()
    def events(self): return tuple(as_event(row) for row in self.entries() if row.get('version')=='approval-event-v1')
    def misses(self): return sum(row.get('type')=='acceptance-proof' and row.get('c_digest')==self.c_digest and row.get('status')=='OBSERVED-MISMATCH' for row in self.entries())
    def usable(self):
        require(not any(row.get('type')=='acceptance-landed' and row.get('c_digest')==self.c_digest for row in self.entries()),'LANDED: task already integrated')
        use=evaluate_use(self.events(),self.grant,len(self.entries()))
        require(self.misses()<3 and use.valid,'REVOKED: three misses, revocation or expiry requires new operator approval')
    def anchor(self, evaluation=None):
        content=dict(self.last_verdict if evaluation is None else {**evaluation.as_record(),'rejections':[]})
        content['journal_head']=self.journal.head()
        private=_regular_read(self.root,'publisher.key').decode()
        require(public_key_for(private)==self.context['identities']['publisher'],'ANCHOR: wrong publisher key')
        record={**content,'record_digest':'sha256:'+canonical_sha256(content)}
        publish_verdict(self.root/'verdict.json',record,root=self.root,signer_id='task-publisher',private_key=private)
        self.last_verdict=content
    def append(self, value, evaluation=None):
        self.journal.append_if_head(self.journal.head(),value if hasattr(value,'as_record') else Record(value))
        self.anchor(evaluation)


@contextmanager
def locked_task(path):
    root=Path(path).absolute()
    require(root==root.resolve() and root.is_dir(),'ABSENT: task directory is missing or aliased')
    fd=os.open(root/'controller.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield Task(root)
    finally: os.close(fd)


def approve(args, previous=None):
    from ranex.cli.main import _command_repository, private_signing_key, subject_digest_for
    source=_command_repository(args)
    try: private=private_signing_key(source)
    except ValueError as exc: refuse('SIGNATURE: '+str(exc))
    owner=public_key_for(private)
    checked=check_bundle(source,Path(args.bundle),args.manifest_digest)
    bundle=Path(args.bundle)
    descriptor=read(bundle/'probe-contract.json')
    require(args.worker_profile in {row['path'] for row in descriptor['entries']},'WORKER: profile must be frozen')
    worker=worker_profile(parse_canonical_payload(_regular_read(bundle,'probes/'+_path(args.worker_profile))),descriptor['roots'])
    argv=descriptor['argv']
    require(len(argv)==5 and argv[:4]==['ranex','specification','observe-http','--profile'],'OBSERVER: task requires the live observer invocation')
    observer_profile=validate_profile(parse_canonical_payload(_regular_read(bundle,'probes/'+_path(argv[4]))))
    state=Path(args.state).absolute()
    require(state==state.resolve() and ',' not in str(state) and not committable_into(state,source),'STATE: external unaliased task directory required')
    require(previous is not None or not state.exists(),'EXISTS: use explicit reapproval; an existing task cannot reset its misses')
    target_ref=checked_git(source,'symbolic-ref','HEAD')
    require(target_ref.startswith('refs/heads/'),'TARGET: approval requires an attached target branch')
    a=read(bundle/'spec-packet.json');b=read(bundle/'manifest.json')
    base=checked['candidate_commit'];subject=subject_digest_for(source,base)
    if previous is not None:
        require(owner==previous.context['owner_key'],'OWNER: reapproval requires the original operator')
        require(a['domain']==previous.context['a']['domain'] and a['task']==previous.context['a']['task'] and a['revision']>previous.context['a']['revision'],'REVISION: same task and strictly newer map required')
        require(str(source)==previous.context['target']['repository'] and target_ref==previous.context['target']['ref'],'TARGET: reapproval cannot change integration target')
    keys={role:generate_keypair() for role in ('worker','evaluator','publisher')}
    identities={role:pair[1] for role,pair in keys.items()};identities['approver']=owner
    if previous is not None:
        keys['publisher']=(_regular_read(state,'publisher.key').decode(),previous.context['identities']['publisher'])
        identities['publisher']=keys['publisher'][1]
    policy=PolicyCapabilities(worker['argv'][0],tuple(worker['argv'][1:]),'.',tuple(worker['product_roots']),('read','write'),tuple(worker['environment']),worker['network'],('*',) if worker['network'] else (),bool(worker['environment']),tuple(worker['environment']),False,False,0)
    capability=policy.as_record();capability.pop('version')
    target={'repository':str(source),'ref':target_ref,'base':base}
    payload=dict(version='approval-payload-v1',domain=a['domain'],task=a['task'],revision=a['revision'],subject_digest=subject,base_digest=subject,a_digest=payload_digest(a),b_digest=payload_digest(b),principal=args.principal,key=owner,role='approver',nonce=uuid.uuid4().hex,journal_predecessor=None,time_window={'not_before':0,'not_after':100000},capability_request=capability,profile_digests={'base':payload_digest(target),'policy':policy.digest,'generator':observer_profile['observer_digest'],'harness':payload_digest({'module':module_digest(),'worker':worker,'identities':identities})})
    envelope={'version':'approval-envelope-v1','payload_type':'application/vnd.ranex.approval-envelope.v1+json','payload':payload,'key_id':owner,'signature':sign_approval_payload(payload,private)}
    if previous is not None:
        previous.append(approval_revoked_event(previous.c_digest,seq=len(previous.entries()),journal_head_link=previous.journal.head(),principal_id=args.principal,key_id=owner,previous_event_digest=previous.events()[-1].digest))
        payload['journal_predecessor']=previous.journal.head()
        payload['time_window']={'not_before':len(previous.entries()),'not_after':len(previous.entries())+100000}
        envelope['signature']=sign_approval_payload(payload,private)
    cd=payload_digest(payload)
    roles=RoleAssignments(tuple(RoleAssignment(role,args.principal if role=='approver' else role,key,role,cd) for role,key in identities.items()))
    issued=issue_approval(a,b,envelope,policy,ApprovalPendingContext(payload_digest(a),subject,args.principal),roles,len(previous.entries()) if previous else 0,previous.journal.head() if previous else None,prior_events=previous.events() if previous else (),prior_event_head=previous.events()[-1].digest if previous else None)
    if previous is not None:
        # Preserve the old revision and journal; a crash fails closed through
        # its revoked authority instead of resetting a task to genesis.
        archive=state/('revision-'+previous.c_digest.removeprefix('sha256:'))
        archive.mkdir(mode=0o700)
        for name in ('bundle','candidate','context.json'):
            shutil.move(state/name,archive/name)
    else:
        state.mkdir(mode=0o700)
    try:
        shutil.copytree(bundle,state/'bundle')
        checked_git(source,'clone','--quiet','--no-local','--no-checkout','--template=',str(source),str(state/'candidate'))
        checked_git(state/'candidate','checkout','--detach',base)
        context=dict(version='acceptance-task-v1',a=a,b=b,c=envelope,owner_key=owner,identities=identities,grant=issued.grant.as_record(),worker=worker,observer_profile=argv[4],command_digest=checked['command_digest'],target=target)
        atomic_writer.write_atomic(state/'context.json',canonical_payload_bytes(context),root=state)
        if previous is None:
            fd=os.open(state/'publisher.key',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream: stream.write(keys['publisher'][0])
        journal=Journal(state/'journal.sqlite3')
        for value in (issued.approved_event,issued.implementable_event,issued.grant_issued_event):journal.append_if_head(journal.head() if (state/'journal.sqlite3').exists() else None,value)
        gate=Gate('live-acceptance','frozen-live-observations',(Claim('live-acceptance',checked['command_digest']),),True)
        evaluation=evaluate(gate,(),subject_digest=subject,catalog_digest=payload_digest(b),approver_id=args.principal)
        content={**evaluation.as_record(),'rejections':[],'journal_head':journal.head()}
        publish_verdict(state/'verdict.json',{**content,'record_digest':'sha256:'+canonical_sha256(content)},root=state,signer_id='task-publisher',private_key=keys['publisher'][0])
    except BaseException:
        if previous is None: shutil.rmtree(state)
        raise
    return {'status':'APPROVED','task':str(state),'c_digest':cd,'base_commit':base}


def reapprove(args):
    with locked_task(args.task) as task:
        args.state=args.task
        return approve(args,previous=task)


def prove(args):
    from ranex.cli.main import subject_digest_for
    with locked_task(args.task) as task:
        task.usable()
        run_id=uuid.uuid4().hex
        task.append({'type':'acceptance-proof-started','c_digest':task.c_digest,'run':run_id})
        try:
            receipt=observe(task.candidate,task.root/'bundle',payload_digest(task.context['b']),task.context['observer_profile'],task.root/('observation-'+run_id))
        except (OSError,ValueError,SubjectError) as exc:
            task.append({'type':'acceptance-proof-error','c_digest':task.c_digest,'run':run_id,'error':str(exc)})
            raise
        commit=receipt['candidate_commit'];subject=subject_digest_for(task.candidate,commit)
        evidence=Evidence('live-acceptance',subject,'evaluator','ranex specification observe-http',receipt['command_digest'],str(Path(sys.modules['ranex.cli.http_observer'].__file__)),0 if receipt['status']=='OBSERVED-MATCH' and receipt['calibrated'] else 1)
        result=evaluate(task.gate,(evidence,),subject_digest=subject,catalog_digest=payload_digest(task.context['b']),approver_id=task.payload['principal'])
        task.append({'type':'acceptance-proof','c_digest':task.c_digest,'run':run_id,'status':receipt['status'],'candidate':commit,'receipt_digest':payload_digest(receipt),'failed_assertion':receipt['failed_assertion'],'evaluation':result.as_record()},result)
        misses=task.misses()
        if misses>=3:
            events=task.events()
            task.append(grant_revoked_event(task.grant,seq=len(task.entries()),journal_head_link=task.journal.head(),principal_id='evaluator',key_id=task.context['identities']['evaluator'],previous_event_digest=events[-1].digest))
        return {'status':'PASS' if result.verdict=='PASS' else 'MISS' if receipt['status']=='OBSERVED-MISMATCH' else 'ERROR','candidate':commit,'misses':misses,'failed_assertion':receipt['failed_assertion'],'journal_head':task.journal.head(),'verdict':str(task.root/'verdict.json')}


def regular_product(root):
    """Bound host-side copying; worker-created links and Git controls are refused."""
    import stat
    size=0;count=0
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            path=Path(directory)/name;mode=path.lstat().st_mode
            require(name not in ('.git','.gitattributes') and (stat.S_ISDIR(mode) or stat.S_ISREG(mode)),'OUTPUT: links, special files and Git controls forbidden')
            if stat.S_ISREG(mode):
                require(path.stat().st_nlink==1,'OUTPUT: hardlinks forbidden')
                size+=path.stat().st_size;count+=1
                require(size<=64*1024*1024 and count<=10000,'OUTPUT: product exceeds copy bound')


def build(args):
    with locked_task(args.task) as task:
        task.usable()
        require(not uncommitted_paths(task.candidate),'DIRTY: candidate must be committed')
        check_bundle(task.candidate,task.root/'bundle',payload_digest(task.context['b']))
        profile=task.context['worker'];run_id=uuid.uuid4().hex
        output=task.root/('build-'+run_id);output.mkdir(mode=0o700)
        name='ranex-build-'+run_id
        env={'PATH':'/usr/bin:/bin','HOME':str(output),'LC_ALL':'C','DOCKER_HOST':'unix:///var/run/docker.sock'}
        commands=[]
        def docker(*argv,timeout=30,required=True):
            result=subprocess.run(['/usr/bin/docker',*argv],env=env,capture_output=True,text=True,timeout=timeout,check=False)
            commands.append({'argv':list(argv),'exit':result.returncode,'stdout':None if 'inspect' in argv[:2] else result.stdout,'stderr':result.stderr})
            require(not required or result.returncode==0,'WORKER: '+result.stderr.strip())
            return result
        base=checked_git(task.candidate,'rev-parse','HEAD')
        task.append({'type':'acceptance-build-started','c_digest':task.c_digest,'run':run_id,'base':base})
        try:
            with materialise_subject(task.candidate,base,safe_git) as subject:
                require(not any(Path(path).name=='.gitattributes' for path in subject.tracked_paths),'ATTRIBUTES: delivery transformations are unsupported')
                mounts=['--mount','type=bind,source='+str(subject.tree)+',target=/workspace,readonly']
                copies=[]
                for index,relative in enumerate(profile['product_roots']):
                    original=subject.tree/relative
                    require(original.is_dir() and original.resolve()==original,'SCOPE: each product root must be an existing regular directory')
                    mutable=output/('root-'+str(index));shutil.copytree(original,mutable)
                    regular_product(mutable);copies.append((relative,mutable))
                    mounts+=['--mount','type=bind,source='+str(mutable)+',target=/workspace/'+relative]
                # Worker variables never enter the host Docker client's environment.
                env_args=[];environment_file=output/'worker.env'
                if profile['environment']:
                    lines=[]
                    for key in profile['environment']:
                        require(key in os.environ,'ENVIRONMENT: approved variable absent: '+key)
                        value=os.environ[key]
                        require('\n' not in value and '\r' not in value,'ENVIRONMENT: multiline values unsupported')
                        lines.append(key+'='+value+'\n')
                    fd=os.open(environment_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'w') as stream:stream.writelines(lines)
                    env_args=['--env-file',str(environment_file)]
                image=json.loads(docker('image','inspect',profile['image']).stdout)[0]
                require(image['Id']==profile['image'],'WORKER: image identity changed')
                declared=image['Config'].get('Volumes') or {}
                require(len(declared)<=16,'WORKER: too many image-declared volumes')
                volume_args=[]
                for destination in declared:
                    require(destination.startswith('/'),'WORKER: absolute image volume required')
                    relative=_path(destination[1:])
                    require(not any(_selected(relative,[name]) or _selected(name,[relative]) for name in ('workspace','tmp','proc','sys','dev')),'WORKER: image volume overlaps a controller mount')
                    # Docker otherwise creates writable anonymous volumes even
                    # with --read-only. Mask image declarations explicitly.
                    volume_args+=['--tmpfs',destination+':ro,noexec,nosuid,size=1048576']
                docker('create','--pull=never','--name',name,'--network','bridge' if profile['network'] else 'none',
                    '--user',str(os.getuid())+':'+str(os.getgid()),'--read-only','--cap-drop','ALL',
                    '--security-opt','no-new-privileges','--memory','512m','--pids-limit','128','--cpus','2',
                    '--tmpfs','/tmp:rw,noexec,nosuid,size=67108864','--log-driver','local','--log-opt','max-size=1m',
                    '--log-opt','max-file=2','--workdir','/workspace','--entrypoint',profile['argv'][0],
                    *mounts,*volume_args,*env_args,profile['image'],*profile['argv'][1:])
                identity=json.loads(docker('inspect',name).stdout)[0]
                require(identity['Image']==profile['image'],'WORKER: image identity changed')
                # Retain only configuration fields without injected secret values.
                recorded={key:identity[key] for key in ('Id','Image','Mounts','HostConfig')}
                docker('start',name)
                waited=docker('wait',name,timeout=profile['timeout_seconds'])
                code=int(waited.stdout.strip())
                # Worker output is untrusted and may contain secrets; retain hashes only.
                logs=subprocess.run(['/usr/bin/docker','logs',name],env=env,capture_output=True,timeout=30,check=False)
                log_hash={'stdout_sha256':hashlib.sha256(logs.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(logs.stderr).hexdigest()}
                docker('rm','-fv',name)
                environment_file.unlink(missing_ok=True)
                require(code==0,'WORKER-EXIT: '+str(code))
                for relative,mutable in copies:
                    regular_product(mutable)
                    destination=task.candidate/relative
                    shutil.rmtree(destination);shutil.copytree(mutable,destination)
                changed=uncommitted_paths(task.candidate)
                require(all(_selected(path,profile['product_roots']) for path in changed),'SCOPE: candidate changes escape approved roots')
                if changed:
                    checked_git(task.candidate,'add','--',*profile['product_roots'])
                    checked_git(task.candidate,'-c','user.name=Ranex worker','-c','user.email=worker@ranex.invalid','commit','-qm','Approved product build '+run_id)
                candidate=checked_git(task.candidate,'rev-parse','HEAD')
                check_bundle(task.candidate,task.root/'bundle',payload_digest(task.context['b']))
                receipt={'version':'acceptance-build-v1','c_digest':task.c_digest,'run':run_id,'base':base,'candidate':candidate,'container':recorded,'logs':log_hash,'commands':commands}
                atomic_writer.write_atomic(output/'receipt.json',canonical_payload_bytes(receipt),root=output)
                task.append({'type':'acceptance-build','c_digest':task.c_digest,'run':run_id,'candidate':candidate,'receipt_digest':payload_digest(receipt)})
                return {'status':'BUILT','candidate':candidate,'receipt':str(output/'receipt.json')}
        except BaseException as exc:
            (output/'worker.env').unlink(missing_ok=True)
            docker('rm','-fv',name,required=False)
            atomic_writer.write_atomic(output/'failure.json',canonical_payload_bytes({'error':str(exc),'commands':commands}),root=output)
            task.append({'type':'acceptance-build-error','c_digest':task.c_digest,'run':run_id,'error':str(exc)})
            raise


def land(args):
    from ranex.cli.main import _checked_out_target_worktree, _worktree_sync_repair
    with locked_task(args.task) as task:
        task.usable()
        require(not uncommitted_paths(task.candidate),'DIRTY: candidate must be committed')
        candidate=checked_git(task.candidate,'rev-parse','HEAD')
        rows=[r for r in task.entries() if r.get('type')=='acceptance-proof' and r.get('c_digest')==task.c_digest]
        require(rows and rows[-1]['candidate']==candidate and rows[-1]['evaluation']['verdict']=='PASS','PASS: latest live proof must pass this exact candidate')
        proof=rows[-1]
        attempts=[r for r in task.entries() if r.get('type')=='acceptance-proof-started' and r.get('c_digest')==task.c_digest]
        require(attempts and attempts[-1]['run']==proof['run'],'PASS: last observation attempt did not complete')
        receipt=read(task.root/('observation-'+proof['run'])/'receipt.json')
        require(payload_digest(receipt)==proof['receipt_digest'] and receipt['candidate_commit']==candidate and receipt['status']=='OBSERVED-MATCH' and receipt['calibrated'],'RECEIPT: live observation changed or is uncalibrated')
        target=task.context['target'];source=Path(target['repository']);ref=target['ref'];base=target['base']
        require(payload_digest(target)==task.payload['profile_digests']['base'],'TARGET: target binding changed')
        require(safe_git(task.candidate,'merge-base','--is-ancestor',base,candidate).returncode==0,'ANCESTRY: candidate is not a fast-forward')
        paths=checked_git(task.candidate,'diff','--name-only',base,candidate).splitlines()
        require(all(_selected(path,task.context['worker']['product_roots']) for path in paths),'SCOPE: unapproved candidate changes')
        check_bundle(task.candidate,task.root/'bundle',payload_digest(task.context['b']))
        worktree=_checked_out_target_worktree(source,ref)
        require(checked_git(source,'rev-parse',ref)==base,'TARGET-MOVED: approve and prove the new integration base')
        if worktree is not None:
            require(not uncommitted_paths(worktree),'DIRTY: integration worktree must be clean')
        checked_git(source,'fetch','--no-write-fetch-head',str(task.candidate),candidate)
        task.append({'type':'acceptance-land-intent','c_digest':task.c_digest,'candidate':candidate,'base':base,'ref':ref,'proof_run':proof['run']})
        updated=safe_git(source,'update-ref',ref,candidate,base)
        require(updated.returncode==0,'TARGET-MOVED: atomic expected-old update refused')
        if worktree is not None:
            try:
                # Same CAS/worktree synchronization used by task merge.
                for argv in (('checkout','--detach',base),('merge','--ff-only',candidate),('symbolic-ref','HEAD',ref)):
                    checked_git(worktree,*argv)
                require(not uncommitted_paths(worktree),'SYNC: integration worktree differs after fast-forward')
            except (OSError,ValueError) as exc:
                repair=_worktree_sync_repair(worktree,base,candidate,ref)
                task.append({'type':'acceptance-land-partial','c_digest':task.c_digest,'candidate':candidate,'error':str(exc),'repair':repair})
                refuse('SYNC: ref advanced but checkout needs repair: '+str(repair))
        require(checked_git(source,'rev-parse',ref)==candidate,'TARGET-MOVED: target changed during synchronization')
        task.append({'type':'acceptance-landed','c_digest':task.c_digest,'candidate':candidate,'ref':ref})
        return {'status':'LANDED','candidate':candidate,'target_ref':ref,'journal_head':task.journal.head()}


def command(args):
    try:
        value={'approve':approve,'prove':prove,'build':build,'reapprove':reapprove,'land':land}[args.task_operation](args)
    except (OSError,ValueError,SubjectError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
        print('E-TASK-REFUSED: '+str(exc),file=sys.stderr);return 2
    print(canonical_payload_bytes(value).decode())
    return 0 if value['status'] in ('APPROVED','BUILT','PASS','LANDED') else 1 if value['status']=='MISS' else 2


def register(root,specification):
    parser=specification.add_parser('approve-task',help='sign and persist an executable acceptance task')
    for name in ('bundle','manifest-digest','worker-profile','state'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--principal',default='owner');parser.add_argument('--external-repository')
    parser.set_defaults(func=command,task_operation='approve')
    parser=root.add_parser('prove',help='run fresh calibrated live acceptance for an approved task')
    parser.add_argument('--task',required=True);parser.set_defaults(func=command,task_operation='prove')

    parser=specification.add_parser('build-task',help='run the approved worker with scoped product writes')
    parser.add_argument('--task',required=True);parser.set_defaults(func=command,task_operation='build')

    parser=specification.add_parser('reapprove-task',help='sign a newer frozen map without erasing prior misses')
    for name in ('bundle','manifest-digest','worker-profile','task'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--principal',default='owner');parser.add_argument('--external-repository')
    parser.set_defaults(func=command,task_operation='reapprove')

    parser=specification.add_parser('land-task',help='fast-forward the approved target to its exact live-passing candidate')
    parser.add_argument('--task',required=True);parser.set_defaults(func=command,task_operation='land')
