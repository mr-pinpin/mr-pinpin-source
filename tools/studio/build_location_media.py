"""Trusted offline receipt-to-registry/descriptor export; no media copies or generation."""
import argparse,hashlib,json,math
from pathlib import Path

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def build(root):
 root=Path(root);receipt=json.loads((root/'receipt.json').read_text());rows={r['path']:r for r in receipt['files']}
 ids={'media/orbit-scrub-v1.mp4':'tractor-orbit-scrub-v1','media/stop-07-panorama.png':'tractor-stop-07-panorama-v1','media/stop-07-source-display.png':'tractor-stop-07-source-display-v1'}
 files={}
 for path,row in rows.items():
  if path.startswith('records/'):
   actual=root/path
   if actual.is_symlink() or actual.stat().st_size!=row['bytes'] or sha(actual)!=row['sha256']:raise ValueError('Delivered record identity differs: '+path)
 for path,identifier in ids.items():
  row=rows[path];actual=root/path
  if actual.is_symlink() or actual.stat().st_size!=row['bytes'] or sha(actual)!=row['sha256']:raise ValueError('Delivered media identity differs: '+identifier)
  files[identifier]={'path':path,'bytes':row['bytes'],'sha256':row['sha256'],'mime':'video/mp4' if path.endswith('.mp4') else 'image/png','name':identifier,'reviewStatus':'recorded' if path.endswith('.mp4') else 'experimental','projection':'camera-path' if path.endswith('.mp4') else 'perspective' if 'source-display' in path else 'equirectangular','provenance':{'sourceReceiptSHA256':sha(root/'receipt.json'),'originalSource':row['source']}}
 records='records/tractor-stops-20260924/'
 selected=json.loads((root/records/'stops/stop-07/selected.json').read_text());frames=json.loads((root/records/'frames-manifest.json').read_text());frame=next(s for s in frames['stops'] if s['id']==selected['id'])
 if selected['id']!='stop-07' or selected.get('status')!='reviewed' or selected['panoramaSha256']!=files[ids['media/stop-07-panorama.png']]['sha256']:raise ValueError('Selected record identity/status differs')
 orbit_record=json.loads((root/'records/tractor-orbit-20260924/orbit-scrub-v1.json').read_text())
 if orbit_record['output']['sha256']!=files[ids['media/orbit-scrub-v1.mp4']]['sha256'] or orbit_record['input']['sha256']!=frames['video']['sha256']:raise ValueError('Orbit derivative/frame provenance differs')
 seconds=frame['actualTimestampSeconds']
 if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<=seconds<orbit_record['output']['duration']:raise ValueError('Explicit actual seconds required')
 ref=lambda identifier:{'id':identifier,'sha256':files[identifier]['sha256']}
 descriptor={'schemaVersion':1,'id':'tractor-stop-07-existing','projection':'equirectangular','reviewStatus':'experimental','camera':selected['sourceCamera'],'orbit':ref(ids['media/orbit-scrub-v1.mp4']),'stops':[{'id':selected['id'],'status':selected['status'],'sourceLockStatus':selected['sourceLockStatus'],'actualTimestampSeconds':seconds,'camera':selected['sourceAnchor']['camera'],'panorama':ref(ids['media/stop-07-panorama.png']),'sourceFrame':ref(ids['media/stop-07-source-display.png'])}],'records':{'selectedSHA256':sha(root/records/'stops/stop-07/selected.json'),'framesManifestSHA256':sha(root/records/'frames-manifest.json'),'reviewSHA256':sha(root/records/'stops/stop-07/source-lock-review.md')}}
 descriptor['sha256']=hashlib.sha256(json.dumps(descriptor,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'schemaVersion':1,'files':files},descriptor
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();registry,descriptor=build(args.root);args.out.mkdir(parents=True,exist_ok=True);(args.out/'media-registry.json').write_text(json.dumps(registry,indent=2)+'\n');(args.out/'location-manifest.json').write_text(json.dumps(descriptor,indent=2)+'\n');print(json.dumps({'files':len(registry['files']),'selectedStop':descriptor['stops'][0]['id'],'actualTimestampSeconds':descriptor['stops'][0]['actualTimestampSeconds'],'selectionSHA256':descriptor['sha256']}))
