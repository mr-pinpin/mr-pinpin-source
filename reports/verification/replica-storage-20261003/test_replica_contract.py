"""Independent black-box contract tests; immutable subject snapshot, synthetic remote."""
import hashlib,importlib.util,json,os,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
SUBJECT_PATH=Path(os.environ.get('REPLICA_QA_CORE', str(Path.cwd()/'packages/replica_store/src/replica_store/core.py')))
spec=importlib.util.spec_from_file_location('replica_qa_subject',SUBJECT_PATH);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
class Remote:
 def __init__(self):self.objects={};self.events=[];self.offline=False;self.corrupt_download=False;self.fail_manifest=False
 def info(self,key):
  self.events.append(('info',key))
  if self.offline:raise OSError('SYNTHETIC_PRIVATE_PROVIDER_TEXT')
  return len(self.objects[key]) if key in self.objects else None
 def upload(self,path,key):
  self.events.append(('upload',key))
  if self.offline or (self.fail_manifest and '/manifests/' in key):raise OSError('SYNTHETIC_PRIVATE_PROVIDER_TEXT')
  self.objects[key]=Path(path).read_bytes()
 def download(self,key,path):
  self.events.append(('download',key))
  if self.offline:raise OSError('SYNTHETIC_PRIVATE_PROVIDER_TEXT')
  data=self.objects[key]
  if self.corrupt_download and '/objects/' in key:data=bytes([data[0]^1])+data[1:]
  Path(path).write_bytes(data)
 def list(self,prefix):
  self.events.append(('list',prefix))
  if self.offline:raise OSError('SYNTHETIC_PRIVATE_PROVIDER_TEXT')
  for key in sorted(self.objects):
   if key.startswith(prefix):yield key,len(self.objects[key])
class ContractChecks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='replica-contract-');self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve()
  self.config={'root':str(self.base/'repo'),'bucket':'synthetic/qa','namespace':'qa/independent','maxObjectBytes':4096,'maxLocalBytes':2_000_000,'minFreeBytes':1,'batchSize':2,'pollReplica':True,'maxRemoteScan':100}
  self.repo=lib.Repository(self.config);self.remote=Remote();self.clock=2_000_000_000
 def art(self,blob=b'version-one',name='asset.bin'):
  p=self.base/name;p.write_bytes(blob);return p,hashlib.sha256(blob).hexdigest(),len(blob)
 def enqueue(self,id='asset',blob=b'version-one',name='asset.bin'):
  p,h,n=self.art(blob,name);self.repo.enqueue(id,p,h,n);return p,h,n
 def once(self,poll=False):
  self.clock+=4000
  with patch.object(lib.time,'time',return_value=self.clock):return self.repo.once(self.remote,poll=poll)
 def inject(self,blob):
  h=hashlib.sha256(blob).hexdigest();self.remote.objects[self.repo.object_key(h)]=blob
  self.remote.objects[self.repo.manifest_key(h)]=lib.json_bytes(self.repo.manifest(h,len(blob)))
  return h,len(blob)
 def partition_zero(self,count=3):
  found=[]
  for i in range(10000):
   b=('partition-zero-'+str(i)).encode();h=hashlib.sha256(b).hexdigest()
   if h.startswith('0'):found.append((h,b))
   if len(found)==count:return sorted(found)
  raise AssertionError('synthetic fixture search failed')
 def poll_rounds(self,n=80):
  for _ in range(n):self.once(poll=True)
 def test_offline_retries_then_source_disappears_successful_owned_bytes(self):
  src,h,n=self.enqueue();src.unlink();self.remote.offline=True
  for _ in range(3):self.once()
  self.assertEqual(self.repo.status('asset',h)['status'],'pending');self.assertEqual(self.repo.resolve(h,n).read_bytes(),b'version-one')
  self.remote.offline=False;self.once();self.assertEqual(self.repo.status('asset',h)['status'],'verified')
 def test_repeated_offline_once_does_not_poison_other_pending_jobs(self):
  _,h,n=self.enqueue();_,second,_=self.enqueue('second',b'version-two','second.bin');self.remote.offline=True
  for _ in range(4):self.once()
  self.remote.offline=False
  for _ in range(3):self.once()
  self.assertEqual(self.repo.status('asset',h)['status'],'verified');self.assertEqual(self.repo.status('second',second)['status'],'verified')
 def test_minis_absence_does_not_prevent_publish_then_cold_replica(self):
  _,h,n=self.enqueue();self.once();self.assertEqual(self.repo.status('asset',h)['status'],'verified')
  reader=lib.Repository(dict(self.config,root=str(self.base/'mini-later')))
  for _ in range(40):reader.once(self.remote,poll=True)
  self.assertEqual(reader.resolve(h,n).read_bytes(),b'version-one')
 def test_immutable_logical_id_rejects_new_sha_without_losing_original_job(self):
  original,h,n=self.enqueue();q,second,m=self.art(b'version-two','second.bin')
  with self.assertRaises(lib.StorageError):self.repo.enqueue('asset',q,second,m)
  self.assertEqual(original.read_bytes(),b'version-one');self.assertEqual(q.read_bytes(),b'version-two')
  self.assertEqual(self.repo.resolve(h,n).read_bytes(),b'version-one')
  self.once();self.assertEqual(self.repo.status('asset',h)['status'],'verified')
  self.assertNotIn(self.repo.object_key(second),self.remote.objects)
 def test_receipt_for_same_size_other_asset_cannot_verify_wrong_sha_request(self):
  _,a,n=self.enqueue('asset-a',b'AAAA','a.bin');_,b,_=self.enqueue('asset-b',b'BBBB','b.bin');self.once()
  self.assertEqual(self.repo.status('asset-a',b)['status'],'absent','asset A never queued digest B; proof for B belongs to different requested identity')
 def test_object_verified_before_manifest_upload_and_private_projection(self):
  _,h,n=self.enqueue();self.once();events=self.remote.events
  self.assertLess(events.index(('download',self.repo.object_key(h))),events.index(('upload',self.repo.manifest_key(h))))
  manifest=json.loads(self.remote.objects[self.repo.manifest_key(h)])
  self.assertEqual(set(manifest),{'schemaVersion','sha256','bytes'});self.assertEqual(manifest['sha256'],h)
 def test_failure_after_verified_object_before_manifest_recovers(self):
  _,h,n=self.enqueue();self.remote.fail_manifest=True;self.once()
  self.assertEqual(self.repo.status('asset',h)['status'],'pending');self.assertNotIn(self.repo.manifest_key(h),self.remote.objects)
  self.remote.fail_manifest=False;self.once();self.assertEqual(self.repo.status('asset',h)['status'],'verified')
 def test_corrupt_object_download_never_publishes_manifest_or_receipt(self):
  src,h,n=self.enqueue();self.remote.corrupt_download=True;self.once()
  self.assertNotIn(self.repo.manifest_key(h),self.remote.objects);self.assertEqual(self.repo.status('asset',h)['status'],'pending');self.assertEqual(src.read_bytes(),b'version-one')
 def test_low_disk_refuses_enqueue_without_owned_art_or_remote_call(self):
  p,h,n=self.art()
  with patch.object(lib.shutil,'disk_usage',return_value=types.SimpleNamespace(free=0)):
   with self.assertRaises(lib.StorageError):self.repo.enqueue('asset',p,h,n)
  self.assertEqual(self.remote.events,[]);self.assertFalse((self.repo.root/'objects'/h).exists());self.assertEqual(p.read_bytes(),b'version-one')
 def test_symlink_source_and_traversal_namespace_refused(self):
  p,h,n=self.art();link=self.base/'linked';link.symlink_to(p)
  with self.assertRaises(lib.StorageError):self.repo.enqueue('asset',link,h,n)
  for namespace in ('../escape','/absolute','a/../../escape','a\\escape'):
   with self.subTest(namespace=namespace):
    with self.assertRaises(lib.StorageError):lib.Repository(dict(self.config,namespace=namespace))
  self.assertEqual(p.read_bytes(),b'version-one')
 def test_forged_job_arbitrary_host_read_path_is_rejected(self):
  p,h,n=self.enqueue();job=next((self.repo.root/'jobs').glob('*.json'));d=json.loads(job.read_text());d['source']=str(p);job.write_text(json.dumps(d))
  with self.assertRaises(lib.StorageError):self.once()
  self.assertEqual(self.remote.events,[])
 def test_late_lexically_earlier_manifest_found_after_durable_wrap(self):
  pairs=self.partition_zero();late= pairs[0];existing=pairs[-1];h,n=self.inject(existing[1]);self.repo.poll(self.remote)
  lateh,laten=self.inject(late[1]);self.repo=lib.Repository(self.config);self.poll_rounds()
  self.assertEqual(self.repo.resolve(lateh,laten).read_bytes(),late[1]);self.assertEqual(self.repo.resolve(h,n).read_bytes(),existing[1])
  before={p.name:p.read_bytes() for p in (self.repo.root/'objects').iterdir()};self.poll_rounds(40)
  self.assertEqual(before,{p.name:p.read_bytes() for p in (self.repo.root/'objects').iterdir()})
 def test_corrupt_first_manifest_cannot_starve_valid_later_records(self):
  pairs=self.partition_zero();bad=pairs[0];good=pairs[-1];gh,gn=self.inject(good[1]);key=self.repo.manifest_key(bad[0]);self.remote.objects[key]=b'{bad json'
  self.poll_rounds(40)
  self.assertTrue((self.repo.root/'objects'/gh).exists(),'corrupt first manifest starved valid later record after forty worker rounds')
  self.assertEqual(self.repo.resolve(gh,gn).read_bytes(),good[1])
 def test_poll_bad_record_has_no_proof_and_repaired_record_recovers_next_wrap(self):
  bad,good=self.partition_zero()[:2];gh,gn=self.inject(good[1]);key=self.repo.manifest_key(bad[0]);self.remote.objects[key]=b'{bad json'
  self.poll_rounds(40)
  self.assertEqual(self.repo.resolve(gh,gn).read_bytes(),good[1])
  self.assertFalse((self.repo.root/'receipts'/(bad[0]+'.json')).exists())
  self.inject(bad[1]);self.repo=lib.Repository(self.config);self.poll_rounds(80)
  self.assertEqual(self.repo.resolve(bad[0],len(bad[1])).read_bytes(),bad[1])
 def test_status_wrong_object_or_manifest_key_never_verified(self):
  _,h,n=self.enqueue();self.once();p=self.repo.root/'receipts'/(h+'.json');original=json.loads(p.read_text())
  for field in ('object','manifest'):
   corrupt=dict(original);corrupt[field]='wrong/identity';p.write_text(json.dumps(corrupt))
   with self.subTest(field=field):self.assertNotEqual(self.repo.status('asset',h)['status'],'verified')
  p.write_text(json.dumps(original));self.assertEqual(self.repo.status('asset',h)['status'],'verified')
 def verify_poll_does_not_refresh_unobserved_remote_bytes(self,corrupt=False):
  h,n=self.inject(b'independent-proof-boundary')
  self.poll_rounds(40)
  receipt=self.repo.root/'receipts'/(h+'.json');before=json.loads(receipt.read_text())
  self.assertTrue(before['remoteVerified']);self.assertEqual(self.repo.resolve(h,n).read_bytes(),b'independent-proof-boundary')
  key=self.repo.object_key(h)
  if corrupt:self.remote.objects[key]=b'X'*n
  else:del self.remote.objects[key]
  self.remote.events=[];self.poll_rounds(40)
  after=json.loads(receipt.read_text()) if receipt.exists() else {}
  self.assertEqual(self.repo.resolve(h,n).read_bytes(),b'independent-proof-boundary')
  fresh_verified=after.get('remoteVerified') is True and after.get('verifiedUTC',0)>before['verifiedUTC']
  self.assertFalse(fresh_verified,'new remoteVerified timestamp issued for missing/corrupt remote bytes; retain historical proof or fresh-download/hash verify')
 def test_poll_existing_replica_missing_remote_object_no_new_remote_proof(self):
  self.verify_poll_does_not_refresh_unobserved_remote_bytes()
 def test_poll_existing_replica_corrupt_remote_object_no_new_remote_proof(self):
  self.verify_poll_does_not_refresh_unobserved_remote_bytes(corrupt=True)
 def test_two_client_distinct_records_and_identical_bytes_do_not_lose_records(self):
  other=lib.Repository(dict(self.config,root=str(self.base/'other-client')))
  p,a,n=self.enqueue('client-one',b'alpha','alpha.bin');q,b,m=self.art(b'beta','beta.bin');other.enqueue('client-two',q,b,m)
  self.once();other.once(self.remote,poll=False)
  self.assertIn(self.repo.manifest_key(a),self.remote.objects);self.assertIn(self.repo.manifest_key(b),self.remote.objects)
  self.repo.enqueue('same-bytes',q,b,m);self.once();self.assertEqual(self.repo.status('same-bytes',b)['status'],'verified')
if __name__=='__main__':
 print('SUBJECT_SHA256='+hashlib.sha256(SUBJECT_PATH.read_bytes()).hexdigest(),flush=True)
 unittest.main(verbosity=2)
