import importlib.util,json,pathlib,tempfile,types,unittest,sys
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('ops',pathlib.Path(__file__).resolve().parents[1]/'chapter_production_ops.py');ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
class Runtime:
 def __init__(self):self.calls=[];self.error=None
 def invoke(self,*args,**kw):
  self.calls.append((args,kw))
  if self.error:raise self.error
  if args[0]=='route':return 201,{'job':JOB,'revision':2}
  return JOB,{'revision':2}
JOB={'id':'job-fixture','status':'claimed','kind':'illustration','chapterId':'chapter-fixture','sceneIds':['scene-1','scene-2'],'claimedBy':'fixture','artifacts':[{'id':'artifact-1','sceneId':'scene-1','type':'image','sha256':'a'*64}]}
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.rt=Runtime();self.store=types.SimpleNamespace(read=lambda:{'revision':1,'jobs':[JOB]},root=self.root)
 def tearDown(self):self.tmp.cleanup()
 def args(self,*argv):return ops.parser().parse_args(list(argv))
 def file(self,name,value):p=self.root/name;p.write_text(value);return str(p)
 def test_resume_is_readonly_and_exposes_remaining(self):
  r=ops.execute(self.args('resume','job-fixture'),self.store,self.rt);self.assertEqual(r['jobs'][0]['remainingSceneIds'],['scene-2']);self.assertFalse(r['mutated']);self.assertFalse(self.rt.calls)
 def test_unknown_resume_fails(self):
  with self.assertRaises(ValueError):ops.execute(self.args('resume','unknown'),self.store,self.rt)
 def test_dispatch_preserves_guard_inputs(self):
  body={'kind':'illustration','chapterId':'chapter-fixture','sceneIds':['scene-1'],'instruction':'fixture','productionScope':'full-production','retryOf':'job-parent'};path=self.file('request.json',json.dumps(body));ops.execute(self.args('dispatch',path),self.store,self.rt);self.assertEqual(self.rt.calls[0][0][-1],body);self.assertEqual(len(self.rt.calls),1)
 def test_business_guard_failure_not_bypassed(self):
  self.rt.error=ValueError('stale go');path=self.file('request.json',json.dumps({'kind':'illustration','chapterId':'c','sceneIds':['s'],'instruction':'fixture'}))
  with self.assertRaises(ValueError):ops.execute(self.args('dispatch',path),self.store,self.rt)
  self.assertEqual(len(self.rt.calls),1)
 def test_no_empty_scene_dispatch(self):
  p=self.file('request.json',json.dumps({'kind':'illustration','chapterId':'c','sceneIds':[],'instruction':'fixture'}))
  with self.assertRaises(ValueError):ops.execute(self.args('dispatch',p),self.store,self.rt)
  self.assertFalse(self.rt.calls)
 def test_complete_records_exact_actual_inputs(self):
  p=self.file('prompt.txt','exact prompt\n');refs=self.file('refs.json',json.dumps([{'assetId':'asset-fixture','roles':['identity']}]))
  ops.execute(self.args('complete','job-fixture','--agent','fixture','--scene','scene-2','--image','native.png','--prompt-file',p,'--references-file',refs,'--tool','image_gen.imagegen'),self.store,self.rt)
  args,kw=self.rt.calls[0];self.assertEqual(args[0],'complete_job');self.assertEqual(kw['actual_prompt'],'exact prompt\n');self.assertEqual(kw['scene_id'],'scene-2');self.assertFalse(kw['visual_pass']);self.assertEqual(kw['actual_references'][0]['roles'],['identity'])
 def test_unknown_reference_shape_never_completes(self):
  p=self.file('prompt.txt','exact');refs=self.file('refs.json','[{}]')
  with self.assertRaises(ValueError):ops.execute(self.args('complete','job-fixture','--agent','fixture','--image','native.png','--prompt-file',p,'--references-file',refs,'--tool','image_gen.imagegen'),self.store,self.rt)
  self.assertFalse(self.rt.calls)
 def test_claim_and_fail_only_explicit(self):
  ops.execute(self.args('claim','job-fixture','--agent','fixture'),self.store,self.rt);self.assertEqual(self.rt.calls[0][0][0],'claim_job')
  ops.execute(self.args('fail','job-fixture','--agent','fixture','--reason','fixture reason'),self.store,self.rt);self.assertEqual(self.rt.calls[1][0][0],'fail_job')
 def test_prepare_wrong_owner_writes_nothing(self):
  p=self.file('prompt.txt','fixture');refs=self.file('refs.json','[]')
  with self.assertRaises(ValueError):ops.execute(self.args('prepare','job-fixture','--agent','other','--scene','scene-2','--prompt-file',p,'--references-file',refs),self.store,self.rt)
  self.assertFalse((self.root/'jobs').exists())
 def test_prepare_persists_prompt_before_generation_without_state_mutation(self):
  p=self.file('prompt.txt','exact fixture prompt\n');refs=self.file('refs.json','[]')
  state={'revision':1,'jobs':[JOB],'assets':[]};self.store.read=lambda:state
  module=types.ModuleType('store');module.atomic_bytes=lambda p,raw:p.write_bytes(raw);module.atomic_json=lambda p,value:p.write_text(json.dumps(value))
  with patch.dict(sys.modules,{'store':module}):
   r=ops.execute(self.args('prepare','job-fixture','--agent','fixture','--scene','scene-2','--prompt-file',p,'--references-file',refs),self.store,self.rt)
  self.assertFalse(r['generationStarted']);self.assertFalse(r['stateMutated']);self.assertEqual(pathlib.Path(r['promptFile']).read_text(),'exact fixture prompt\n');self.assertEqual(state['revision'],1);self.assertFalse(self.rt.calls)
 def test_prepare_unsafe_scene_writes_nothing(self):
  p=self.file('prompt.txt','fixture');refs=self.file('refs.json','[]')
  with self.assertRaises(ValueError):ops.execute(self.args('prepare','job-fixture','--agent','fixture','--scene','../../escape','--prompt-file',p,'--references-file',refs),self.store,self.rt)
  self.assertFalse((self.root/'jobs').exists())
 def test_oversized_request_rejected(self):
  p=self.file('huge','a'*(ops.MAX_REQUEST+1))
  with self.assertRaises(ValueError):ops.read_file(p,ops.MAX_REQUEST)
if __name__=='__main__':unittest.main()
