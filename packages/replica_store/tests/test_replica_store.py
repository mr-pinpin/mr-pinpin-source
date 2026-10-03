import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from replica_store import Repository,StorageError
from replica_store.core import atomic_json,read_json

class Remote:
    def __init__(self):self.objects={};self.events=[];self.offline=False;self.corrupt=False;self.crash=False
    def info(self,key):
        if self.offline:raise ConnectionError('offline')
        return len(self.objects[key]) if key in self.objects else None
    def upload(self,path,key):
        self.objects[key]=Path(path).read_bytes();self.events.append(('upload',key))
        if self.crash and '/objects/' in key:self.crash=False;raise ConnectionError('crash after object')
    def download(self,key,destination):
        data=self.objects[key];self.events.append(('download',key))
        if self.corrupt and '/objects/' in key:data=b'x'+data[1:]
        Path(destination).write_bytes(data)
    def list(self,prefix):
        if self.offline:raise ConnectionError('offline')
        yield from [(k,len(v)) for k,v in sorted(self.objects.items()) if k.startswith(prefix)]

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.remote=Remote()
        self.cfg={'root':str(self.root/'outbox'),'bucket':'approved/art','namespace':'replica-v1','minFreeBytes':1,'maxLocalBytes':1000000,'maxObjectBytes':10000,'batchSize':2,'maxRemoteScan':100}
        self.repo=Repository(self.cfg)
    def tearDown(self):self.temp.cleanup()
    def asset(self,data=b'picture',identifier='image'):
        path=self.root/(identifier+'.png');path.write_bytes(data);sha=hashlib.sha256(data).hexdigest()
        self.repo.enqueue(identifier,path,sha,len(data));return sha,len(data),path
    def retry(self,repo=None):
        repo=repo or self.repo
        for path in repo.path('jobs').glob('*.json'):
            value=read_json(path);value['nextAttemptUTC']=0;atomic_json(path,value)
    def test_owned_bytes_without_host_source(self):
        sha,size,path=self.asset();path.unlink();job=read_json(next(self.repo.path('jobs').glob('*.json')))
        self.assertNotIn('source',job);self.assertNotIn(str(self.root),json.dumps(job))
        self.repo.once(self.remote,False);self.assertEqual(self.repo.status('image',sha)['status'],'verified')
    def test_offline_bounded_retry_then_recovery(self):
        sha,_,_=self.asset();self.remote.offline=True;self.repo.once(self.remote,False)
        job=read_json(next(self.repo.path('jobs').glob('*.json')));self.assertEqual(job['attempts'],1)
        self.repo.once(self.remote,False);self.assertEqual(read_json(next(self.repo.path('jobs').glob('*.json')))['attempts'],1)
        self.assertEqual(self.repo.status('image',sha)['status'],'pending')
        self.remote.offline=False;self.retry();self.repo.once(self.remote,False);self.assertEqual(self.repo.status('image',sha)['status'],'verified')
    def test_crash_after_object_before_manifest_recovery(self):
        sha,_,_=self.asset();self.remote.crash=True;self.repo.once(self.remote,False)
        self.assertIn(self.repo.object_key(sha),self.remote.objects);self.assertNotIn(self.repo.manifest_key(sha),self.remote.objects)
        self.retry();self.repo.once(self.remote,False);self.assertEqual(self.repo.status('image',sha)['status'],'verified')
    def test_corrupt_remote_never_publishes_manifest(self):
        sha,_,_=self.asset();self.remote.corrupt=True;self.repo.once(self.remote,False)
        self.assertNotIn(self.repo.manifest_key(sha),self.remote.objects);self.assertEqual(self.repo.status('image',sha)['status'],'pending')
    def test_fresh_verify_before_manifest_and_private_projection(self):
        sha,_,_=self.asset();self.repo.once(self.remote,False)
        events=self.remote.events;self.assertLess(events.index(('download',self.repo.object_key(sha))),events.index(('upload',self.repo.manifest_key(sha))))
        self.assertEqual(set(json.loads(self.remote.objects[self.repo.manifest_key(sha)])),{'schemaVersion','sha256','bytes'})
        before=len(events);self.repo.once(self.remote,False);self.assertEqual(len(events),before)
    def test_two_clients_no_shared_index_or_overwrite(self):
        first,_,_=self.asset();self.repo.once(self.remote,False)
        other=Repository(dict(self.cfg,root=str(self.root/'other')))
        second=hashlib.sha256(b'second').hexdigest();source=self.root/'second.png';source.write_bytes(b'second')
        other.enqueue('second',source,second,6);other.once(self.remote,False)
        self.assertIn(other.manifest_key(second),self.remote.objects);self.assertIn(self.repo.manifest_key(first),self.remote.objects)
        other.enqueue('same-content',self.root/'image.png',first,7);other.once(self.remote,False)
        self.assertEqual(other.status('same-content',first)['status'],'verified')
    def test_poll_atomic_replica_and_late_record(self):
        sha,size,_=self.asset();self.repo.once(self.remote,False)
        replica=Repository(dict(self.cfg,root=str(self.root/'replica'),pollReplica=True))
        for _ in range(32):replica.once(self.remote)
        self.assertEqual(replica.resolve(sha,size).read_bytes(),b'picture')
        later,late_size,_=self.asset(b'late','later');self.repo.once(self.remote,False)
        for _ in range(32):replica.once(self.remote)
        self.assertEqual(replica.resolve(later,late_size).read_bytes(),b'late')
    def test_corrupt_existing_replica_preserved(self):
        sha,size,_=self.asset();self.repo.once(self.remote,False)
        replica=Repository(dict(self.cfg,root=str(self.root/'replica'),pollReplica=True));target=replica.path('objects/'+sha);target.parent.mkdir();target.write_bytes(b'corrupt')
        atomic_json(replica.path('poll.json'),{'partition':int(sha[0],16),'offset':0})
        result=replica.once(self.remote);self.assertEqual(result[-1]['poll'],'pending');self.assertEqual(target.read_bytes(),b'corrupt')
    def test_low_disk_and_budget_refusal(self):
        path=self.root/'input';path.write_bytes(b'picture');sha=hashlib.sha256(b'picture').hexdigest()
        with patch('replica_store.core.shutil.disk_usage',return_value=SimpleNamespace(free=0)):
            with self.assertRaises(StorageError):self.repo.enqueue('image',path,sha,7)
        small=Repository(dict(self.cfg,root=str(self.root/'small'),maxLocalBytes=1))
        with self.assertRaises(StorageError):small.enqueue('image',path,sha,7)
    def test_traversal_symlinks_and_arbitrary_host_path_job(self):
        with self.assertRaises(StorageError):self.repo.path('../private')
        target=self.repo.path('objects');target.symlink_to(self.root)
        with self.assertRaises(StorageError):self.repo.path('objects/file')
        target.unlink();sha,_,_=self.asset();job_path=next(self.repo.path('jobs').glob('*.json'));job=read_json(job_path);job['source']='/private/host-file';atomic_json(job_path,job)
        with self.assertRaises(StorageError):self.repo.once(self.remote,False)
        self.assertFalse(self.remote.objects)
    def test_conflicting_ids_hash_guard_and_oversize(self):
        sha,_,path=self.asset();path.write_bytes(b'different');other=hashlib.sha256(b'different').hexdigest()
        with self.assertRaises(StorageError):self.repo.enqueue('image',path,other,9)
        self.assertNotEqual(self.repo.status('image',other)['status'],'verified')
        with self.assertRaises(StorageError):self.repo.enqueue('huge',path,other,10001)
    def test_targeted_cli_put_skips_old_backlog(self):
        import sys
        from replica_store import cli
        self.cfg['batchSize']=1
        config=self.root/'config.json';config.write_text(json.dumps(self.cfg))
        old,_,_=self.asset(identifier='old')
        source=self.root/'requested.png';source.write_bytes(b'requested');sha=hashlib.sha256(b'requested').hexdigest()
        with patch.object(cli,'HFRemote',return_value=self.remote),patch.object(sys,'argv',['replica-store','--config',str(config),'put','requested',str(source),sha,'9']):cli.main()
        self.assertIn(self.repo.manifest_key(sha),self.remote.objects)
        self.assertNotIn(self.repo.manifest_key(old),self.remote.objects)
        self.assertEqual(self.repo.status('requested',sha)['status'],'verified')
    def test_cold_get_identity_corruption_and_offline(self):
        sha,size,_=self.asset();self.repo.once(self.remote,False)
        reader=Repository(dict(self.cfg,root=str(self.root/'reader')))
        self.remote.corrupt=True
        with self.assertRaises(StorageError):reader.get(self.remote,sha,size)
        self.assertFalse(reader.path('objects/'+sha).exists())
        self.remote.corrupt=False
        with self.assertRaises(StorageError):reader.get(self.remote,sha,size+1)
        self.remote.offline=True
        with self.assertRaises(ConnectionError):reader.get(self.remote,sha,size)
        self.remote.offline=False
        self.assertEqual(reader.get(self.remote,sha,size).read_bytes(),b'picture')
        self.assertTrue(read_json(reader.path('receipts/'+sha+'.json'))['remoteVerified'])
    def test_wrong_sha_status_is_absent(self):
        a,_,_=self.asset(b'AAAA','a');b,_,_=self.asset(b'BBBB','b');self.repo.once(self.remote,False)
        self.assertEqual(self.repo.status('a',b)['status'],'absent')
    def test_poll_preserves_historical_proof_and_requires_remote_without_proof(self):
        sha,size,_=self.asset();self.repo.once(self.remote,False)
        receipt=self.repo.path('receipts/'+sha+'.json');historical=receipt.read_bytes()
        self.remote.objects.pop(self.repo.object_key(sha))
        atomic_json(self.repo.path('poll.json'),{'partition':int(sha[0],16),'offset':0})
        self.repo.poll(self.remote)
        self.assertEqual(receipt.read_bytes(),historical)
        # Only isolated test evidence is removed; local bytes cannot prove remote existence.
        receipt.unlink()
        for blob in (None,b'corrupt'):
            if blob is not None:self.remote.objects[self.repo.object_key(sha)]=blob
            atomic_json(self.repo.path('poll.json'),{'partition':int(sha[0],16),'offset':0})
            result=self.repo.poll(self.remote)
            self.assertEqual(result['poll'],'pending');self.assertFalse(receipt.exists())
        self.remote.objects[self.repo.object_key(sha)]=b'picture'
        atomic_json(self.repo.path('poll.json'),{'partition':int(sha[0],16),'offset':0})
        self.repo.poll(self.remote);self.assertTrue(read_json(receipt)['remoteVerified'])
    def test_manifest_conflict_refused(self):
        sha,_,_=self.asset();self.remote.objects[self.repo.manifest_key(sha)]=b'private bogus record'
        self.repo.once(self.remote,False);self.assertEqual(self.repo.status('image',sha)['status'],'pending')
        self.assertEqual(self.remote.objects[self.repo.manifest_key(sha)],b'private bogus record')

if __name__=='__main__':unittest.main()
