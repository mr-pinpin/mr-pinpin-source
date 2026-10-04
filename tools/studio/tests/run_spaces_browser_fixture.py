"""Root-run actual Studio opaque-frame Spaces QA. No provider or live server."""
import os,sys,json,shutil,hashlib,subprocess,threading,tempfile
from pathlib import Path
import argparse
ARGS=argparse.ArgumentParser(description='Provider-disabled actual Studio Spaces browser acceptance. No live app/provider.')
ARGS.add_argument('--kernel-dir',type=Path,required=True);ARGS.add_argument('--media-root',type=Path,required=True);ARGS.add_argument('--out-root',type=Path,required=True);ARGS.add_argument('--node',default='/opt/homebrew/bin/node');ARGS.add_argument('--prepare-only',action='store_true');opts=ARGS.parse_args()
STUDIO=Path(__file__).resolve().parents[1];ROOT=opts.out_root.resolve();ROOT.mkdir(parents=True,exist_ok=True);MEDIA=opts.media_root.resolve();STABLE=opts.kernel_dir.resolve();sys.path.insert(0,str(STABLE))
from immutable_bundle import verify_bundle,capture,publish_bundle
manifest=verify_bundle(STABLE);receipt={'path':str(STABLE),'stableRelease':manifest['hash']}
from store import Store
from server import Handler
from workspace_runtime import WorkspaceRuntime
from business_runtime import BusinessRuntime
from http.server import ThreadingHTTPServer
QA=Path(tempfile.mkdtemp(prefix='studio-spaces-',dir=ROOT));(ROOT/'latest-spaces-fixture-path.txt').write_text(str(QA)+'\n')
cache=QA/'media-cache';cache.mkdir();import importlib.util
selector=importlib.util.spec_from_file_location('_fixture_descriptor_builder',STUDIO/'build_location_media.py');builder=importlib.util.module_from_spec(selector);selector.loader.exec_module(builder);registry,descriptor=builder.build(MEDIA)
for row in registry['files'].values():
 target=cache/row['path'];target.parent.mkdir(parents=True,exist_ok=True);os.link(MEDIA/row['path'],target) # exact local immutable bytes, no duplicate38MB
(cache/'media-registry.json').write_text(json.dumps(registry));(cache/'location-manifest.json').write_text(json.dumps(descriptor))
os.environ['PINPIN_MEDIA_CACHE_ROOT']=str(cache)
# Capture both source trees, then confirm they stayed unchanged before using copies.
for attempt in range(3):
 business_files=capture(STUDIO/'business',exclude=('tests',));workspace_files=capture(STUDIO/'web/workspace-dev')
 if business_files==capture(STUDIO/'business',exclude=('tests',)) and workspace_files==capture(STUDIO/'web/workspace-dev'):break
else:raise RuntimeError('Source is changing; retry after coherent exports are applied')
from model import now
bm=publish_bundle(business_files,QA/'inputs/business',now(),'fixture-business');wm=publish_bundle(workspace_files,QA/'inputs/workspace',now(),'fixture-workspace')
source=QA/'inputs/business'/bm['hash'];workspace=QA/'inputs/workspace'/wm['hash'];base_sha=hashlib.sha256((source/'capability_registry.py').read_bytes()).hexdigest()
store=Store(QA/'data');before=store.read();business=BusinessRuntime(source,QA/'runtime',watch=False)
if not business.active:raise RuntimeError('Business activation failed: '+str(business.snapshot()))
if 'spaces.location.get.v1' not in [o['id'] for o in business.capabilities()['operations']]:raise RuntimeError('Actual registry is disconnected: merge spaces.location.get.v1 through registry owner first')
workspace_runtime=WorkspaceRuntime(workspace,QA/'runtime',receipt['stableRelease'])
parent=QA/'parent.html';parent.write_text('''<!doctype html><meta charset="utf-8"><style>iframe{width:100%;height:100vh;border:0}body{margin:0}</style><div id="workspace-controls"></div><div id="workspace-host"></div><div id="notification"></div><script type="module">
import {createWorkspaceHost} from '/shell-frame-host.js';
const state=await(await fetch('/api/state')).json();const studio={state,route:{view:'spaces',lang:'en',ui:'live'},sceneIds:[],assetIds:[],entityId:null};
window.qaProviderCalls=0;window.qaDraft='Unsaved original composer';window.qaSeq=1;window.qaHost=createWorkspaceHost({studio,getConversation:()=>({conversation:{messages:[],status:'idle'},draft:window.qaDraft,draftSeq:window.qaSeq,pending:false,uploading:false}),onDraft:d=>{window.qaDraft=d.text;window.qaSeq=d.seq;},onConversationCommand:()=>{window.qaProviderCalls++;throw Error('Provider forbidden in isolated fixture');}});
</script>''')
class QAHandler(Handler):
 def _route(self,method):
  if method=='GET' and self.path.startswith('/qa-spaces'):return self._file(parent,'text/html; charset=utf-8')
  return super()._route(method)
if opts.prepare_only:
 report={'qaRoot':str(QA),'stableRelease':receipt['stableRelease'],'businessHash':business.active.sha,'capabilityIds':[r['id'] for r in business.capabilities()['operations']],'providerInitialized':False,'liveLaunch':False,'preparedOnly':True}
 (ROOT/'spaces-fixture-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));business.close();workspace_runtime.close();sys.exit(0)
server=ThreadingHTTPServer(('127.0.0.1',0),QAHandler);server.store=store;server.web_root=STABLE/'web';server.business_runtime=business;server.runtime=workspace_runtime;server.stable_release=receipt['stableRelease'];server.conversation=None
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 import urllib.request
 range_response=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+'/api/media/files/tractor-orbit-scrub-v1',headers={'Range':'bytes=0-15'}),timeout=10)
 assert range_response.status==206 and range_response.headers['Content-Type'].startswith('video/mp4') and len(range_response.read())==16
 env=dict(os.environ,STUDIO_SPACES_QA_URL='http://127.0.0.1:'+str(server.server_port)+'/qa-spaces',STUDIO_SPACES_QA_OUT=str(QA))
 result=subprocess.run([opts.node,str(STUDIO/'web/tests/browser-studio-spaces.cjs')],env=env,timeout=120)
 after=store.read();assert after==before,'Read-only Spaces QA changed Store';assert not after['jobs'];
 report={'qaRoot':str(QA),'stableRelease':receipt['stableRelease'],'businessHash':business.active.sha,'baseRegistrySHA256':base_sha,'providerInitialized':False,'storeUnchanged':True,'jobs':0,'productionAuthorizations':0,'liveLaunch':False,'browserExitCode':result.returncode,'existingMediaRange206Verified':True}
 (QA/'studio-spaces-acceptance-receipt.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/'studio-spaces-acceptance-receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(result.returncode)
finally:server.shutdown();server.server_close();business.close();workspace_runtime.close()
