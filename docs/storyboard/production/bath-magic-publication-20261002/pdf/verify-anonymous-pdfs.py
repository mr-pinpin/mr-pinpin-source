from pathlib import Path
import json,urllib.request,hashlib,time,concurrent.futures
p=Path("/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-pdf-release-20261002");catalog=json.loads((p/'catalog-entry.json').read_text())
def verify(item):
 lang,e=item;h=hashlib.sha256();n=0;prefix=b''
 req=urllib.request.Request(e['url'],headers={'Origin':'https://mr-pinpin.github.io'})
 with urllib.request.urlopen(req,timeout=120) as r:
  status=r.status;ctype=r.headers.get('Content-Type');cors=r.headers.get('Access-Control-Allow-Origin')
  while b:=r.read(1024*1024):
   if not prefix:prefix=b[:5]
   h.update(b);n+=len(b)
 assert prefix==b'%PDF-' and n==e['bytes'] and h.hexdigest()==e['sha256']
 return {'lang':lang,'url':e['url'],'status':status,'bytes':n,'sha256':h.hexdigest(),'contentType':ctype,'cors':cors,'anonymous':True,'pdfMagic':True,'verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(verify,catalog['pdf'].items()))
(p/'anonymous-pdf-verification.json').write_text(json.dumps({'verified':True,'authentication':'none; urllib requests with no auth headers or credentials','entries':rows},indent=2)+'\n');print(json.dumps(rows))