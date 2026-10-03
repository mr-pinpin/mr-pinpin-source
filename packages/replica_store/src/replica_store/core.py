"""Durable verified byte outbox and optional HF-polled replica; no deletion."""
import contextlib,fcntl,hashlib,json,os,re,shutil,stat,tempfile,time
from pathlib import Path

class StorageError(ValueError): pass
def digest(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{64}',value): raise StorageError('Invalid SHA256')
    return value
def safe(root,relative):
    if not isinstance(relative,str) or not relative or '\\' in relative or any(p in ('','.','..') for p in relative.split('/')) or relative.startswith('/'):
        raise StorageError('Invalid relative path')
    path=Path(root)
    for part in [*path.parents,path]:
        if part.is_symlink(): raise StorageError('Symlink root')
    for part in relative.split('/'):
        path=path/part
        if path.is_symlink(): raise StorageError('Symlink component')
    return path
def read_json(path,limit=16384):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): raise StorageError('Nonregular JSON')
        raw=stream.read(limit+1)
    if len(raw)>limit: raise StorageError('Oversized JSON')
    return json.loads(raw)
def identity(path,max_bytes):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    h=hashlib.sha256();size=0
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>max_bytes: raise StorageError('Invalid/oversized regular object')
        for block in iter(lambda:stream.read(1024*1024),b''):
            size+=len(block)
            if size>max_bytes: raise StorageError('Oversized object')
            h.update(block)
    return h.hexdigest(),size
def checked(path,sha,size):
    if identity(path,size)!=(digest(sha),size): raise StorageError('Content conflict/corruption')
def json_bytes(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink():raise StorageError('Symlink destination')
    fd,name=tempfile.mkstemp(prefix='.record-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(json_bytes(value));stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
    finally:
        if os.path.exists(name):os.unlink(name)
def immutable_place(temp,destination,sha,size):
    checked(temp,sha,size);destination.parent.mkdir(parents=True,exist_ok=True)
    try:os.link(temp,destination,follow_symlinks=False)
    except FileExistsError:checked(destination,sha,size)
    fd=os.open(destination.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)

class Repository:
    def __init__(self,config):
        self.config=dict(config);self.root=Path(config['root']).expanduser()
        safe(self.root,'objects')
        if not self.root.is_absolute():raise StorageError('Configured root must be absolute')
        if not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',config.get('bucket','')):raise StorageError('Invalid bucket')
        ns=config.get('namespace','');safe(self.root,ns)
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_./-]{0,199}',ns):raise StorageError('Invalid namespace')
        self.namespace=ns
        self.maximum=config.get('maxObjectBytes',41943040);self.budget=config.get('maxLocalBytes',1073741824)
        self.floor=config.get('minFreeBytes',2147483648);self.batch=config.get('batchSize',4)
        for value in (self.maximum,self.budget,self.floor,self.batch):
            if type(value)!=int or value<=0:raise StorageError('Invalid bounds')
        if self.batch>64 or self.maximum>1024**3:raise StorageError('Excessive bounds')
        self.root.mkdir(parents=True,exist_ok=True)
    def path(self,relative):return safe(self.root,relative)
    @contextlib.contextmanager
    def lock(self):
        path=self.path('worker.lock');fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(stream,fcntl.LOCK_UN)
    def preflight(self,required):
        total=0;count=0
        for directory,dirs,files in os.walk(self.root,followlinks=False):
            for name in dirs+files:
                path=Path(directory)/name
                if path.is_symlink():raise StorageError('Symlink in repository')
            for name in files:
                count+=1
                if count>100000:raise StorageError('Repository scan bound exceeded')
                total+=(Path(directory)/name).stat().st_size
        if total+required>self.budget:raise StorageError('Local byte budget exhausted; no eviction performed')
        if shutil.disk_usage(self.root).free<self.floor+required:raise StorageError('Low disk reserve')
    def object_key(self,sha):return self.namespace+'/objects/'+digest(sha)
    def manifest_key(self,sha):return self.namespace+'/manifests/'+digest(sha)[0]+'/'+sha+'.json'
    def manifest(self,sha,size):
        if type(size)!=int or not 0<=size<=self.maximum:raise StorageError('Invalid object size')
        return {'schemaVersion':1,'sha256':digest(sha),'bytes':size}
    def validate_manifest(self,value):
        if not isinstance(value,dict) or set(value)!={'schemaVersion','sha256','bytes'} or value['schemaVersion']!=1:raise StorageError('Invalid immutable manifest')
        return self.manifest(value['sha256'],value['bytes'])
    def enqueue(self,asset_id,source,sha,size):
        self.manifest(sha,size)
        if not isinstance(asset_id,str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}',asset_id):raise StorageError('Invalid logical ID')
        # Caller reads its source in its own process; jobs never authorize host paths.
        source=Path(source)
        for parent in [source,*source.parents]:
            if parent.is_symlink():raise StorageError('Symlink source')
        checked(source,sha,size)
        job_id=hashlib.sha256(asset_id.encode()).hexdigest();target=self.path('jobs/'+job_id+'.json')
        with self.lock():
            existing=read_json(target) if target.exists() else None
            if existing and any(existing.get(k)!=v for k,v in [('assetId',asset_id),('sha256',sha),('bytes',size)]):raise StorageError('Logical ID content conflict')
            owned=self.path('objects/'+sha)
            if not owned.exists():
                self.preflight(size*2+16384);owned.parent.mkdir(parents=True,exist_ok=True)
                fd,name=tempfile.mkstemp(prefix='.owned-',dir=owned.parent)
                try:
                    with os.fdopen(fd,'wb') as output:
                        source_fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
                        with os.fdopen(source_fd,'rb') as stream:
                            copied=0
                            for block in iter(lambda:stream.read(1024*1024),b''):
                                copied+=len(block)
                                if copied>size:raise StorageError('Source grew during copy')
                                output.write(block)
                        output.flush();os.fsync(output.fileno())
                    immutable_place(Path(name),owned,sha,size)
                finally:os.unlink(name)
            checked(owned,sha,size)
            job=existing or {'schemaVersion':1,'assetId':asset_id,'sha256':sha,'bytes':size,'status':'pending','attempts':0,'nextAttemptUTC':0}
            self.preflight(16384);atomic_json(target,job)
        return self.status(asset_id,sha)
    def status(self,asset_id,sha):
        digest(sha);job_id=hashlib.sha256(asset_id.encode()).hexdigest()
        job_path=self.path('jobs/'+job_id+'.json')
        job=read_json(job_path) if job_path.exists() else None
        if job and (job.get('assetId')!=asset_id or job.get('sha256')!=sha):job=None
        proof_path=self.path('receipts/'+sha+'.json')
        proof=read_json(proof_path) if proof_path.exists() else None
        verified=bool(job and job.get('assetId')==asset_id and job.get('sha256')==sha and proof and proof.get('bucket')==self.config['bucket'] and proof.get('namespace')==self.namespace and proof.get('sha256')==sha and proof.get('bytes')==job.get('bytes') and proof.get('remoteVerified') is True and proof.get('object')==self.object_key(sha) and proof.get('manifest')==self.manifest_key(sha))
        return {'assetId':asset_id,'sha256':sha,'bytes':job.get('bytes') if job else None,'status':'verified' if verified else 'pending' if job else 'absent','receipt':proof if verified else None}
    def resolve(self,sha,size):
        self.manifest(sha,size);path=self.path('objects/'+sha);checked(path,sha,size);return path
    def get(self,remote,sha,size):
        expected=self.manifest(sha,size)
        with self.lock():
            owned=self.path('objects/'+sha)
            if owned.exists():return self.resolve(sha,size)
            self.preflight(size*2+32768)
            with tempfile.TemporaryDirectory(prefix='.get-',dir=self.root) as directory:
                temp=Path(directory);key=self.manifest_key(sha);length=remote.info(key)
                if type(length)!=int or not 0<length<=512:raise StorageError('Missing/oversized immutable manifest')
                self.download(remote,key,temp/'manifest',length)
                if self.validate_manifest(read_json(temp/'manifest',512))!=expected:raise StorageError('Requested manifest identity mismatch')
                self.download(remote,self.object_key(sha),temp/'object',size)
                immutable_place(temp/'object',owned,sha,size)
            proof=dict(expected,bucket=self.config['bucket'],namespace=self.namespace,object=self.object_key(sha),manifest=key,remoteVerified=True,verifiedUTC=time.time(),origin='hf-get')
            atomic_json(self.path('receipts/'+sha+'.json'),proof)
            return owned
    def download(self,remote,key,destination,size):
        self.preflight(size+16384)
        info=remote.info(key)
        if info is None or info!=size or size>self.maximum:raise StorageError('Missing/oversized remote object')
        remote.download(key,destination)
        if destination.stat().st_size!=size:raise StorageError('Remote download size changed')
    def publish(self,remote,sha,size):
        owned=self.resolve(sha,size);self.preflight(size+32768)
        with tempfile.TemporaryDirectory(prefix='.transfer-',dir=self.root) as directory:
            temp=Path(directory);key=self.object_key(sha);info=remote.info(key)
            if info is None:remote.upload(owned,key)
            elif info!=size:raise StorageError('Remote content conflict')
            self.download(remote,key,temp/'verify',size);checked(temp/'verify',sha,size)
            manifest=self.manifest(sha,size);encoded=json_bytes(manifest);mk=self.manifest_key(sha)
            info=remote.info(mk)
            if info is None:
                (temp/'manifest').write_bytes(encoded);remote.upload(temp/'manifest',mk)
            elif info!=len(encoded):raise StorageError('Remote immutable manifest conflict')
            self.download(remote,mk,temp/'manifest-check',len(encoded))
            if (temp/'manifest-check').read_bytes()!=encoded:raise StorageError('Remote immutable manifest conflict')
        proof=dict(manifest,bucket=self.config['bucket'],namespace=self.namespace,object=key,manifest=mk,remoteVerified=True,verifiedUTC=time.time())
        atomic_json(self.path('receipts/'+sha+'.json'),proof)
        return proof
    def once(self,remote,poll=True,asset_id=None):
        results=[]
        with self.lock():
            self.preflight(32768)
            jobs=self.path('jobs');processed=0
            for path in ([self.path('jobs/'+hashlib.sha256(asset_id.encode()).hexdigest()+'.json')] if asset_id is not None else sorted(jobs.glob('*.json')) if jobs.exists() else []):
                if processed>=self.batch:break
                job=read_json(path)
                if set(job)-{'schemaVersion','assetId','sha256','bytes','status','attempts','nextAttemptUTC','errorType'}:raise StorageError('Unrecognized outbox fields; host paths forbidden')
                self.manifest(job['sha256'],job['bytes'])
                if path.stem!=hashlib.sha256(job['assetId'].encode()).hexdigest():raise StorageError('Job filename mismatch')
                if self.status(job['assetId'],job['sha256'])['status']=='verified' or job.get('nextAttemptUTC',0)>time.time():continue
                processed+=1
                try:
                    self.publish(remote,job['sha256'],job['bytes']);job.update(status='verified',nextAttemptUTC=0);job.pop('errorType',None)
                except Exception as exc:
                    attempts=job.get('attempts',0)+1
                    job.update(status='pending',attempts=attempts,nextAttemptUTC=time.time()+min(3600,5*2**min(attempts,9)),errorType=type(exc).__name__)
                atomic_json(path,job);results.append({'assetId':job['assetId'],'status':job['status']})
            if poll and self.config.get('pollReplica',False):
                try:results.append(self.poll(remote))
                except Exception as exc:results.append({'poll':'pending','errorType':type(exc).__name__})
        return results
    def poll(self,remote):
        cp=self.path('poll.json');cursor=read_json(cp) if cp.exists() else {'partition':0,'offset':0}
        partition=cursor['partition'];offset=cursor['offset'];maximum_scan=self.config.get('maxRemoteScan',10000)
        if type(partition)!=int or not 0<=partition<16 or type(offset)!=int or not 0<=offset<=maximum_scan:raise StorageError('Invalid poll cursor')
        prefix=self.namespace+'/manifests/'+format(partition,'x')+'/'
        entries=iter(remote.list(prefix));skipped=0
        for _ in range(offset):
            try:next(entries);skipped+=1
            except StopIteration:break
        done=0;exhausted=False;failures=0
        while done<self.batch and skipped+done<maximum_scan:
            try:key,size=next(entries)
            except StopIteration:exhausted=True;break
            try:
                if not re.fullmatch(re.escape(prefix)+'[a-f0-9]{64}\\.json',key) or type(size)!=int or not 0<size<=512:raise StorageError('Unsafe remote manifest')
                with tempfile.TemporaryDirectory(prefix='.poll-',dir=self.root) as directory:
                    temp=Path(directory);self.download(remote,key,temp/'manifest',size)
                    m=self.validate_manifest(read_json(temp/'manifest',512));sha=m['sha256']
                    if self.manifest_key(sha)!=key:raise StorageError('Manifest key mismatch')
                    owned=self.path('objects/'+sha)
                    receipt_path=self.path('receipts/'+sha+'.json')
                    historical=read_json(receipt_path) if receipt_path.exists() else None
                    matching=bool(historical and all(historical.get(k)==v for k,v in dict(m,bucket=self.config['bucket'],namespace=self.namespace,object=self.object_key(sha),manifest=key,remoteVerified=True).items()) and type(historical.get('verifiedUTC')) in (int,float))
                    if owned.exists():
                        checked(owned,sha,m['bytes'])
                        if not matching:
                            self.download(remote,self.object_key(sha),temp/'object',m['bytes'])
                            checked(temp/'object',sha,m['bytes'])
                    else:
                        self.preflight(m['bytes']*2+16384)
                        self.download(remote,self.object_key(sha),temp/'object',m['bytes'])
                        immutable_place(temp/'object',owned,sha,m['bytes'])
                        matching=False
                    proof=dict(m,bucket=self.config['bucket'],namespace=self.namespace,object=self.object_key(sha),manifest=key,remoteVerified=True,verifiedUTC=time.time(),origin='hf-poll')
                    if not matching:atomic_json(receipt_path,proof)
            except Exception as exc:
                failures+=1
                self.preflight(16384)
                atomic_json(self.path('poll-failure-'+format(partition,'x')+'.json'),{'entryDigest':hashlib.sha256(str(key).encode()).hexdigest(),'errorType':type(exc).__name__,'observedUTC':time.time(),'remoteVerified':False})
            done+=1
        if skipped+done>=maximum_scan and not exhausted:raise StorageError('Remote partition scan bound reached; narrow configured namespace')
        atomic_json(cp,{'partition':(partition+1)%16 if exhausted else partition,'offset':0 if exhausted else offset+done})
        return {'poll':'pending' if failures else 'verified','objects':done-failures,'failedEntries':failures,'partition':partition}
