"""Isolated real HTTP/immutable-runtime tests; no live Store or generation.
STUDIO_QA_STABLE points at the original stable dependency tree for export tests.
After source mapping, run python3 -m unittest discover -s tools/studio/tests -p test_business_extensions.py.
"""
import subprocess
import copy, hashlib, http.client, importlib.util, json, os, pathlib, shutil, sys, tempfile, threading, time, types, unittest
HERE=pathlib.Path(__file__).resolve().parent
CORE=HERE if (HERE/'business_runtime.py').exists() else HERE.parent
BASE=pathlib.Path(os.environ.get('STUDIO_QA_STABLE',str(CORE)))
sys.path[:0]=[str(CORE),str(BASE)]
from business_contract import metadata, bounded_json, value_valid
from business_runtime import BusinessRuntime, _Handle
from model import StudioError
from server import Handler
from http.server import ThreadingHTTPServer

class StoreFixture:
    def __init__(self,root):
        self.root=pathlib.Path(root);self.asset=self.root/'reference.png';self.asset.write_bytes(b'fixture-original-public-art')
        raw=self.asset.read_bytes()
        self.state={'revision':0,'assets':[{'id':'art','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'provenance':{}}],
            'events':[],'project':{'chapters':[],'entities':[{'id':'place','kind':'location'},{'id':'pinpin','kind':'character','referenceIds':['art']}]}}
        self.snapshots={}
    def read(self): return copy.deepcopy(self.state)
    def asset_path(self,*args): return self.asset
    def save_project(self,project,expected):
        if expected!=self.state['revision']:raise StudioError('Conflict','revision_conflict',409)
        self.state['project']=copy.deepcopy(project);self.state['revision']+=1
        self.state['events'].append({'type':'project.snapshot','revision':self.state['revision']})
        self.snapshots[self.state['revision']]={'project':copy.deepcopy(project)}
        return self.read()
    def project_revision(self,revision): return copy.deepcopy(self.snapshots[revision])

class ExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=pathlib.Path(cls.tmp.name)
        package=root/'example_business';package.mkdir();(package/'__init__.py').write_text('')
        business=pathlib.Path(os.environ.get('STUDIO_QA_BUSINESS',str(CORE/'business')))
        for name in ('capability_adapters.py','draft_pdf_delivery.py'):
            shutil.copyfile(CORE/'business'/name,package/name)
        shutil.copyfile(business/'chapter_drafts.py',package/'chapter_drafts.py')
        spec=importlib.util.spec_from_file_location('example_business',package/'__init__.py',submodule_search_locations=[str(package)])
        module=importlib.util.module_from_spec(spec);sys.modules['example_business']=module;spec.loader.exec_module(module)
        import example_business.capability_adapters as adapters
        import example_business.chapter_drafts as drafts
        cls.adapters=adapters;cls.drafts=drafts
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setUp(self):
        self.fixture=tempfile.TemporaryDirectory();self.store=StoreFixture(self.fixture.name)
        spec={'title':'Fixture','synopsis':'','location':{'baseEntityId':'place','description':'A field','proposed':False},'referenceIds':['art'],
              'panels':[{'id':'p1','action':'Watch','cause':'Leaf falls','effect':'Leaf lands','caption':'Hmm…','camera':'Close','beat':'setup','seconds':5,'castIds':['pinpin'],'previewKind':'reused-reference','imageAssetId':'art'}]}
        self.drafts.save_draft(self.store,{'chapterId':'fixture','spec':spec,'expectedRevision':0,'baseVersion':0})
        self.runtime=BusinessRuntime.__new__(BusinessRuntime);self.runtime.lock=threading.RLock();self.runtime.read_only=False
        self.runtime.previous=None;self.runtime.handles=[];self.runtime.active=None
        self.handle=_Handle('a'*64,'fixture',types.SimpleNamespace(business_dispatch=self.adapters.business_dispatch),capabilities=metadata(self.adapters.business_capabilities(),'a'*64))
        self.runtime.active=self.handle;self.runtime.handles=[self.handle]
        self.http=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.http.store=self.store;self.http.business_runtime=self.runtime
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
    def tearDown(self): self.http.shutdown();self.http.server_close();self.fixture.cleanup()
    def call(self,operation='draft.get.v1',body=None,sha=None,readOnly=False,revision=None,method='POST',headers=None):
        client=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=2)
        context={'Content-Type':'application/json','X-Studio-Business-Hash':sha or self.handle.sha,'X-Studio-Revision':str(self.store.read()['revision'] if revision is None else revision),'X-Studio-Read-Only':str(readOnly).lower()}
        context.update(headers or {})
        client.request(method,'/api/business/'+operation,json.dumps(body or {'chapterId':'fixture'}).encode() if method=='POST' else None,context)
        response=client.getresponse();result=(response.status,json.loads(response.read()));client.close();return result
    def patch(self):
        version=self.store.read()['project']['chapters'][0]['studioDraft']['versions'][-1]
        return {'chapterId':'fixture','baseVersion':version['version'],'baseSHA256':version['sha256'],'expectedRevision':self.store.read()['revision'],'patches':[{'panelId':'p1','fields':{'caption':'Quietly.'}}]}
    def test_trusted_metadata_real_http(self):
        status,value=self.call('capabilities',method='GET');self.assertEqual(status,200);self.assertEqual(value['businessHash'],self.handle.sha);self.assertEqual(len(value['operations']),4)
    def test_actual_get_and_patch(self):
        status,value=self.call();self.assertEqual(status,200);self.assertEqual(value['draft']['panels'][0]['caption'],'Hmm…')
        status,value=self.call('draft.patch.v1',self.patch());self.assertEqual(status,200);self.assertEqual(value['version'],2);self.assertFalse(value['productionStarted'])
    def test_stale_hash_never_invokes_handler(self):
        before=self.store.read();status,_=self.call('draft.patch.v1',self.patch(),sha='b'*64);self.assertEqual(status,409);self.assertEqual(self.store.read(),before)
    def test_historical_mutation_refused_server_side(self):
        status,_=self.call('draft.patch.v1',self.patch(),readOnly=True);self.assertEqual(status,403)
    def test_old_revision_mutation_refused_even_without_readonly(self):
        status,_=self.call('draft.patch.v1',self.patch(),revision=0);self.assertEqual(status,403)
    def test_historical_get_is_bound_to_snapshot(self):
        self.call('draft.patch.v1',self.patch());status,value=self.call(readOnly=True,revision=1);self.assertEqual(status,200);self.assertEqual(value['draft']['currentVersion'],1);self.assertTrue(value['readOnly'])
    def test_authorization_requires_explicit_go_and_no_generation(self):
        v=self.store.read()['project']['chapters'][0]['studioDraft']['versions'][-1]
        body={'chapterId':'fixture','version':v['version'],'sha256':v['sha256'],'referenceHash':v['referenceHash'],'expectedRevision':1,'explicitFullProductionGo':False,'userInstruction':'Fixture only'}
        status,_=self.call('draft.authorize.v1',body);self.assertEqual(status,400)
        body['explicitFullProductionGo']=True;status,value=self.call('draft.authorize.v1',body);self.assertEqual(status,200);self.assertFalse(value['productionStarted'])
    def test_pdf_chunk_existing_registered_fixture(self):
        root=self.store.root/'deliveries';root.mkdir();raw=b'%PDF-1.4\nfixture only';(root/'fixture.pdf').write_bytes(raw)
        v=self.store.read()['project']['chapters'][0]['studioDraft']['versions'][-1]
        entry={'chapterId':'fixture','version':1,'sourceVersionSHA256':v['sha256'],'language':'en','artifactSHA256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'storagePath':'fixture.pdf'}
        (root/'catalog.json').write_text(json.dumps({'schemaVersion':1,'deliveries':[entry]}))
        body={k:entry[k] for k in ('chapterId','version','sourceVersionSHA256','language','artifactSHA256')};body['offset']=0
        status,result=self.call('draft.pdf.chunk.v1',body);self.assertEqual(status,200);self.assertEqual(result['artifactSHA256'],entry['artifactSHA256']);self.assertTrue(result['done'])
    def test_schema_unknown_field_refused(self): self.assertEqual(self.call(body={'chapterId':'fixture','path':'/tmp'})[0],400)
    def test_origin_guard_preserved(self): self.assertEqual(self.call(headers={'Origin':'https://evil.test'})[0],403)
    def test_unknown_method_refused(self): self.assertEqual(self.call(method='GET')[0],404)
    def test_declared_request_limit_refused(self): self.assertEqual(self.call(body={'chapterId':'fixture','huge':'x'*40000})[0],413)
    def test_response_cap_enforced(self):
        self.handle.module=types.SimpleNamespace(business_dispatch=lambda *args:{'data':'x'*1048577})
        self.assertEqual(self.call()[0],413)
    def test_timeout_is_uncertain_and_not_replayed(self):
        calls=[];self.handle.capabilities['operations'][1]['timeoutMs']=20
        def slow(*args): calls.append(1);time.sleep(.2);return {'ok':True}
        self.handle.module=types.SimpleNamespace(business_dispatch=slow)
        self.assertEqual(self.call('draft.patch.v1',self.patch())[0],504)
        self.assertEqual(self.call('draft.patch.v1',self.patch())[0],409)
        self.assertEqual(len(calls),1);time.sleep(.25);self.assertEqual(self.handle.leases,0)
    def test_lease_pins_old_handler_across_activation(self):
        entered=threading.Event();release=threading.Event();result=[]
        def old(*args): entered.set();release.wait(1);return {'revision':'old'}
        self.handle.module=types.SimpleNamespace(business_dispatch=old)
        thread=threading.Thread(target=lambda:result.append(self.call()));thread.start();self.assertTrue(entered.wait(1))
        new=_Handle('b'*64,'new',types.SimpleNamespace(business_dispatch=lambda *args:{'revision':'new'}),capabilities=metadata(self.adapters.business_capabilities(),'b'*64))
        with self.runtime.lock:self.runtime.previous=self.handle;self.runtime.active=new;self.runtime.handles.append(new)
        release.set();thread.join();self.assertEqual(result[0][1]['revision'],'old');self.assertEqual(self.call(sha='a'*64)[0],409)
    def test_one_mib_request_descriptor_supported(self):
        op=copy.deepcopy(self.adapters.business_capabilities()[0]);op['maxRequestBytes']=1048576
        self.assertEqual(metadata([op],self.handle.sha)['operations'][0]['maxRequestBytes'],1048576)
    def test_real_immutable_package_activation(self):
        source=pathlib.Path(self.fixture.name)/'package';source.mkdir()
        for name in ('capability_adapters.py','draft_pdf_delivery.py'):
            shutil.copyfile(CORE/'business'/name,source/name)
        business=pathlib.Path(os.environ.get('STUDIO_QA_BUSINESS',str(CORE/'business')))
        shutil.copyfile(business/'chapter_drafts.py',source/'chapter_drafts.py')
        (source/'__init__.py').write_text('from .capability_adapters import business_capabilities,business_dispatch\nAPI_VERSION=1\ndef selected_context(a,b):return {}\ndef route(a,b,c,d,e):return None\ndef self_test():return True\n')
        runtime=BusinessRuntime(source,pathlib.Path(self.fixture.name)/'runtime',watch=False)
        try:
            self.assertIsNotNone(runtime.active)
            meta=runtime.capabilities();self.assertEqual(len(meta['operations']),4)
            raw=runtime.capability_request(self.store,'draft.get.v1',meta['businessHash'],b'{"chapterId":"fixture"}',{'readOnly':False,'revision':1})
            self.assertEqual(json.loads(raw)['draft']['currentVersion'],1)
        finally:runtime.close()
    def test_large_declared_request_above_64k(self):
        op={'id':'fixture.batch.v1','effect':'read','method':'POST','maxRequestBytes':1048576,'maxResponseBytes':100,'timeoutMs':1000,
            'request':{'type':'object','fields':{'items':{'type':'array','maxItems':128,'items':{'type':'text','maxLength':1500}}},'required':['items']}}
        self.handle.capabilities=metadata([op],self.handle.sha)
        self.handle.module=types.SimpleNamespace(business_dispatch=lambda store,op,body,context:{'count':len(body['items'])})
        status,result=self.call('fixture.batch.v1',{'items':['x'*1500]*100});self.assertEqual(status,200);self.assertEqual(result['count'],100)
    def test_body_above_generic_one_mib_refused(self):
        client=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=2)
        client.putrequest('POST','/api/business/draft.get.v1')
        for key,value in {'Content-Type':'application/json','Content-Length':'1048577','X-Studio-Business-Hash':self.handle.sha,'X-Studio-Revision':'1','X-Studio-Read-Only':'false'}.items():client.putheader(key,value)
        client.endheaders()  # No body sent: refusal must happen before reading it.
        response=client.getresponse();self.assertEqual(response.status,413);response.read();client.close()
    def test_real_js_bridge_to_python_http(self):
        data={'url':'http://127.0.0.1:'+str(self.http.server_port),'patch':self.patch()}
        script = """
import assert from 'node:assert/strict';
import {fetchCapabilities,executeBusinessRequest} from './web/business-extension-contract.js';
import {validateRequest} from './web/shell-bridge.js';
const data=JSON.parse(process.argv[1]);globalThis.location={origin:data.url};
const transport=(path,options)=>fetch(data.url+path,options);
const registry=await fetchCapabilities(transport);
let action=validateRequest('/api/business/draft.get.v1',{method:'POST',body:JSON.stringify({chapterId:'fixture'})},true,false,registry);
let result=await executeBusinessRequest(action,registry,{revision:1,readOnly:false,canMutate:true},transport);
assert.equal(result.draft.currentVersion,1);
action=validateRequest('/api/business/draft.patch.v1',{method:'POST',body:JSON.stringify(data.patch)},true,false,registry);
result=await executeBusinessRequest(action,registry,{revision:1,readOnly:false,canMutate:true},transport);
assert.equal(result.version,2);assert.equal(result.productionStarted,false);
console.log('real JS->HTTP->immutable business get/patch passed');
"""
        result=subprocess.run(['node','--input-type=module','-e',script,json.dumps(data)],cwd=CORE,capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('passed',result.stdout)
    def test_fixed_state_route_remains_available(self):
        client=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=2)
        client.request('GET','/api/state');response=client.getresponse()
        self.assertEqual(response.status,200);self.assertEqual(json.loads(response.read())['revision'],1);client.close()
    def test_legacy_business_mutation_blocked_during_uncertain_capability(self):
        self.handle.mutation_pending=True
        client=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=2)
        client.request('POST','/api/plan/approve',b'{}',{'Content-Type':'application/json'})
        response=client.getresponse();self.assertEqual(response.status,409);response.read();client.close()
    def test_pure_rejects_nonfinite_bool_bounds_and_paths(self):
        op=copy.deepcopy(self.adapters.business_capabilities()[0]);op['maxRequestBytes']=True
        with self.assertRaises(StudioError): metadata([op],self.handle.sha)
        with self.assertRaises(StudioError): bounded_json({'n':float('nan')},100)
        op=copy.deepcopy(self.adapters.business_capabilities()[0]);op['request']['fields']['url']={'type':'text','maxLength':100}
        with self.assertRaises(StudioError): metadata([op],self.handle.sha)

if __name__=='__main__':unittest.main()
