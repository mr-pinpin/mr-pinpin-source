"""Read-only, bounded PDF JSON chunks from a registered immutable draft receipt.

New business helper only. App owns route wiring/catalog registration. No file path
is accepted from the request; files stay beneath Store.root/deliveries.
"""
import base64,hashlib,json,re
from pathlib import Path
from model import StudioError
MAX_PDF=64*1024*1024
CHUNK=64*1024
_verified={}
def fail(message):raise StudioError(message,'delivery_invalid',400)
def integer(value):
 if type(value) is int:return value
 if isinstance(value,str) and value.isdigit() and len(value)<=10:return int(value)
 fail('Invalid bounded integer')
def _chunk(store,request):
 if not isinstance(request,dict) or any(k not in {'chapterId','version','sourceVersionSHA256','language','artifactSHA256','offset'} for k in request):fail('Invalid delivery selection')
 chapter=request.get('chapterId');version=integer(request.get('version'));language=request.get('language');source=request.get('sourceVersionSHA256');artifact=request.get('artifactSHA256');offset=integer(request.get('offset',0))
 if not isinstance(chapter,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',chapter) or not 1<=version<=100 or language not in ('en','ru'):fail('Invalid delivery binding')
 if any(not isinstance(h,str) or not re.fullmatch('[a-f0-9]{64}',h) for h in (source,artifact)):fail('Require full version/artifact SHA')
 state=store.read();c=next((c for c in state['project']['chapters'] if c['id']==chapter),None);v=next((v for v in (c or {}).get('studioDraft',{}).get('versions',[]) if v['version']==version),None)
 if not v or v.get('sha256')!=source:fail('Saved version binding differs')
 store_root=Path(store.root).resolve();root=(store_root/'deliveries').resolve()
 if not root.is_relative_to(store_root):fail('Delivery root invalid')
 catalog=root/'catalog.json'
 if not catalog.resolve().is_relative_to(root):fail('Delivery catalog path invalid')
 if not catalog.is_file() or catalog.stat().st_size>256*1024:fail('Delivery catalog missing/bounded')
 entries=json.loads(catalog.read_text()).get('deliveries',[])
 if not isinstance(entries,list) or len(entries)>1024 or not all(isinstance(x,dict) for x in entries):fail('Delivery catalog bound exceeded')
 entry=next((x for x in entries if all(x.get(k)==value for k,value in [('chapterId',chapter),('version',version),('sourceVersionSHA256',source),('language',language),('artifactSHA256',artifact)])),None)
 if not entry:fail('No registered export for this exact version/artifact')
 relative=Path(entry.get('storagePath',''))
 if relative.is_absolute() or '..' in relative.parts:fail('Registered delivery path invalid')
 p=(root/relative).resolve()
 if not p.is_relative_to(root) or p.suffix!='.pdf' or not p.is_file():fail('Registered delivery absent/invalid')
 stat=p.stat();total=entry.get('bytes')
 if type(total) is not int or not 1<=total<=MAX_PDF or stat.st_size!=total:fail('PDF byte size mismatch/bound exceeded')
 if offset<0 or offset>=total or offset%CHUNK:fail('Invalid PDF chunk offset')
 signature=(str(p),stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_ino)
 if _verified.get(artifact)!=signature:
  h=hashlib.sha256()
  with p.open('rb') as f:
   if f.read(5)!=b'%PDF-':fail('Not a PDF')
   f.seek(0)
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  if h.hexdigest()!=artifact:fail('PDF checksum mismatch')
  if len(_verified)>=256:_verified.pop(next(iter(_verified)))
  _verified[artifact]=signature
 with p.open('rb') as f:f.seek(offset);data=f.read(min(CHUNK,total-offset))
 # Recheck signature after reading, avoid returning bytes if file changed meanwhile.
 after=p.stat()
 if signature!=(str(p),after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_ino):fail('PDF changed while reading')
 result={'schemaVersion':1,'chapterId':chapter,'version':version,'sourceVersionSHA256':source,'language':language,'artifactSHA256':artifact,'totalBytes':total,'offset':offset,'bytes':len(data),'chunkSHA256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode(),'mime':'application/pdf','filename':chapter[:60]+'-v'+str(version)+'-'+language+'.pdf','done':offset+len(data)==total,'unpublished':True}
 if len(json.dumps(result).encode())>96*1024:fail('Response chunk bound exceeded')
 return result

def chunk(store,request):
 try:return _chunk(store,request)
 except StudioError:raise
 except (OSError,ValueError,TypeError,KeyError):fail("Delivery receipt invalid or unavailable")


def list_deliveries(store,chapter):
 """Sanitized registered identities only; chunk() verifies actual bytes on download."""
 root=Path(store.root).resolve();directory=(root/'deliveries').resolve()
 catalog=directory/'catalog.json'
 if not directory.is_relative_to(root) or not catalog.resolve().is_relative_to(directory):
  return [], 'invalid-catalog'
 if not catalog.is_file():return [], 'no-catalog'
 if catalog.stat().st_size>256*1024:return [], 'invalid-catalog'
 try:
  entries=json.loads(catalog.read_text()).get('deliveries',[])
 except (OSError,ValueError,AttributeError):return [], 'invalid-catalog'
 if not isinstance(entries,list) or len(entries)>1024:return [], 'invalid-catalog'
 bindings={v['version']:v['sha256'] for v in chapter.get('studioDraft',{}).get('versions',[])}
 result=[]
 for entry in entries:
  if not isinstance(entry,dict) or entry.get('chapterId')!=chapter['id']:continue
  version=entry.get('version')
  if type(version) is not int or bindings.get(version)!=entry.get('sourceVersionSHA256') or entry.get('language') not in ('en','ru') or not isinstance(entry.get('artifactSHA256'),str) or not re.fullmatch('[a-f0-9]{64}',entry['artifactSHA256']) or type(entry.get('bytes')) is not int or not 1<=entry['bytes']<=MAX_PDF:continue
  result.append({k:entry[k] for k in ('chapterId','version','sourceVersionSHA256','language','artifactSHA256','bytes')})
 return result,'registered'


def delivery_context(store,request):
 """Exact immutable chapter + bounded selected registry for local unpublished export."""
 if not isinstance(request,dict) or set(request)-{'chapterId','version','sourceVersionSHA256','additionalAssetIds'}:fail('Invalid delivery context selectors')
 chapter_id=request.get('chapterId');version=integer(request.get('version'));digest=request.get('sourceVersionSHA256')
 if not isinstance(chapter_id,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',chapter_id) or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):fail('Exact chapter/version/hash required')
 state=store.read();chapter=next((c for c in state['project']['chapters'] if c['id']==chapter_id),None)
 saved=next((v for v in (chapter or {}).get('studioDraft',{}).get('versions',[]) if v['version']==version),None)
 if not saved or saved.get('sha256')!=digest:fail('Exact saved chapter version differs')
 # Return only metadata; export verifies actual selected bytes. No resolution/network.
 extras=request.get('additionalAssetIds',[])
 if not isinstance(extras,list) or len(extras)>5 or any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',x) for x in extras):fail('Invalid selected supplemental assets')
 ids=set(extras);ids.update(p.get('imageAssetId') for p in saved['spec'].get('panels',[]));ids.add(saved['spec'].get('coverAssetId'))
 assets=[{k:a[k] for k in ('id','storagePath','mime','bytes','sha256','reviewStatus') if k in a} for a in state['assets'] if a['id'] in ids]
 for a in assets:
  original=next(x for x in state['assets'] if x['id']==a['id'])
  a['provenance']={k:original.get('provenance',{}).get(k) for k in ('kind','source','sourceAssetId') if k in original.get('provenance',{})}
 result={'record':{'id':chapter_id,'studioDraft':{'versions':[saved]}},'assets':assets,'projectRevision':state['revision'],'sourceVersionSHA256':digest,'workflow':{'guide':'workflows/pilot-delivery.md','command':'tools/studio-python tools/studio-delivery/cli.py --chapter CHAPTER --version N --sha256 EXACT --cover ID --miniature ID --coloring ID1 --coloring ID2 --coloring ID3 --out EXTERNAL_NEW_DIR','generation':False,'publication':False,'missingAssets':'Explicit missing inputs reject completed delivery; draft mode retains labeled gaps'},'unpublished':True}
 if len(json.dumps(result,ensure_ascii=False).encode())>8*1024*1024:fail('Delivery context exceeds8MiB; narrow registry required')
 return result

def cli_delivery_route(store,method,path,query,body):
 if path!='/api/draft-delivery/context':return None
 if method!='GET' or set(query)-{'chapterId','version','sourceVersionSHA256','additionalAssetIds'} or not {'chapterId','version','sourceVersionSHA256'}.issubset(query) or any(not isinstance(v,list) or len(v)!=1 or not isinstance(v[0],str) for v in query.values()):fail('Invalid delivery context route')
 request={k:v[0] for k,v in query.items()}
 if 'additionalAssetIds' in request:
  try:request['additionalAssetIds']=json.loads(request['additionalAssetIds'])
  except ValueError:fail('Invalid supplemental asset selection')
 return 200,delivery_context(store,request)

def delivery_workflow_hint(chapter):
 """Concise opt-in selected chapter guidance, no filesystem/Store access."""
 versions=chapter.get('studioDraft',{}).get('versions',[])
 version=next((v for v in versions if v['version']==chapter.get('studioDraft',{}).get('currentVersion')),None)
 if not version:return {'ready':False,'guide':'workflows/pilot-delivery.md','reason':'No saved chapter draft'}
 return {'guide':'workflows/pilot-delivery.md','chapterId':chapter['id'],'version':version['version'],'sourceVersionSHA256':version['sha256'],'helper':'tools/studio-python tools/studio-delivery/cli.py','requiredInputs':['registered cover','registered miniature/contact sheet','three distinct registered line-art pages','actual panel imageAssetId bytes','explicit EN/RU text'],'commandArguments':['--chapter',chapter['id'],'--version',str(version['version']),'--sha256',version['sha256'],'--cover','COVER_ID','--miniature','MINIATURE_ID','--coloring','LINE1','--coloring','LINE2','--coloring','LINE3','--out','EXTERNAL_NEW_DIR','--render','--node','EXISTING_NODE','--playwright-module','EXISTING_MODULE'],'stateWrites':False,'generation':False,'publication':False,'readiness':'Inputs checked during build; this hint is not byte verification'}
