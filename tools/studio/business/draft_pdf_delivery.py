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
