#!/usr/bin/env python3
"""Deterministic unpublished reader from a pinned saved chapter record (stdlib)."""
import argparse,base64,hashlib,html,json,re
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def esc(text):return html.escape(str(text),quote=True)
def localized(value,lang):
 if isinstance(value,str):return value
 if isinstance(value,dict):return value.get(lang,'')
 return ''
def fingerprint(value):return digest(json.dumps(value,sort_keys=True,ensure_ascii=False).encode())
def selected_version(document,chapter,version):
 # Support actual Store snapshot/chapter schema as well as chapter-bound saved record.
 project=document.get('project')
 if isinstance(project,dict):
  selected=next((c for c in project.get('chapters',[]) if c.get('id')==chapter),None)
 elif document.get('id')==chapter and 'studioDraft' in document:selected=document
 else:selected=None
 if selected is not None:
  record=next((v for v in selected.get('studioDraft',{}).get('versions',[]) if v.get('version')==version),None)
  if record is None:raise ValueError('Saved version absent')
 elif document.get('chapterId',document.get('spec',{}).get('chapterId'))==chapter:record=document
 else:raise ValueError('Saved chapter mismatch; export a chapter-bound record or snapshot')
 if type(record.get('version')) is not int or record['version']!=version:raise ValueError('Saved version mismatch')
 bindings=record.get('referenceBindings');reference_hash=record.get('referenceHash')
 if bindings is not None or reference_hash is not None:
  if not isinstance(bindings,list) or not isinstance(reference_hash,str):raise ValueError('Incomplete saved reference binding')
  expected=fingerprint([{k:b[k] for k in ('assetId','sha256','bytes','roles')} for b in bindings])
  if expected!=reference_hash or fingerprint({'spec':record['spec'],'referenceHash':reference_hash})!=record.get('sha256'):raise ValueError('Saved spec/reference SHA mismatch')
 return record

def prepare(record_path,record_sha,chapter,version,registry,asset_root,out,lang='en',coloring=(),cover_asset=None,max_embedded_bytes=256*1024*1024):
 if lang not in ('en','ru'):raise ValueError('Language must be en or ru')
 raw=Path(record_path).read_bytes()
 if len(raw)>8*1024*1024 or digest(raw)!=record_sha:raise ValueError('Saved record SHA/size mismatch')
 record=selected_version(json.loads(raw),chapter,version);spec=record['spec']
 if type(record.get('version')) is not int or type(version) is not int or version<1:raise ValueError('Invalid saved version')
 if record.get('version')!=version:raise ValueError('Saved version mismatch')
 panels=spec['panels']
 if not isinstance(panels,list) or not 1<=len(panels)<=512:raise ValueError('Require1–512 ordered panels')
 ids=[p['id'] for p in panels]
 if len(set(ids))!=len(ids):raise ValueError('Duplicate panel ID')
 if len(coloring)>3:raise ValueError('Only three coloring slots')
 root=Path(asset_root).resolve();out=Path(out).resolve()
 if out==Path(__file__).parent.resolve() or out.is_relative_to(Path(__file__).parent.resolve()):raise ValueError('Output must be outside source directory')
 if out.exists() and any(out.iterdir()):raise ValueError('Output must be new/empty; never overwrite')
 if type(max_embedded_bytes) is not int or max_embedded_bytes<1:raise ValueError('Invalid embedded-byte budget')
 assets={a['id']:a for a in registry};missing=[];used=[];captions=[];embedded_bytes=0
 def image(identifier,slot):
  nonlocal embedded_bytes
  if not identifier:missing.append({'slot':slot,'assetId':None,'reason':'not-selected'});return '<div class="missing">Missing artwork · '+esc(slot)+'</div>'
  a=assets.get(identifier)
  if not a:missing.append({'slot':slot,'assetId':identifier,'reason':'not-registered'});return '<div class="missing">Missing artwork · '+esc(identifier)+'</div>'
  relative=Path(a['storagePath'])
  if relative.is_absolute() or '..' in relative.parts:raise ValueError('Asset path forbidden')
  path=(root/relative).resolve()
  if not path.is_relative_to(root):raise ValueError('Asset path forbidden')
  if not path.is_file():missing.append({'slot':slot,'assetId':identifier,'reason':'bytes-absent'});return '<div class="missing">Missing artwork · '+esc(identifier)+'</div>'
  b=path.read_bytes();mime=a['mime']
  if mime not in ('image/png','image/jpeg','image/webp') or not 0<len(b)<=40*1024*1024:raise ValueError('Unsupported artwork type/size')
  if digest(b)!=a['sha256'] or len(b)!=a['bytes']:raise ValueError('Artwork SHA/size mismatch')
  binding=next((x for x in record.get('referenceBindings',[]) if x['assetId']==identifier),None)
  if binding and (binding['sha256']!=a['sha256'] or binding['bytes']!=a['bytes']):raise ValueError('Selected art differs from saved reference binding')
  embedded_bytes+=len(b)
  if embedded_bytes>max_embedded_bytes:raise ValueError('Embedded artwork budget exceeded; no silent omission')
  proof={k:a.get(k) for k in ('id','sha256','bytes','mime','reviewStatus')};proof['slot']=slot;proof['provenance']={k:a.get('provenance',{}).get(k) for k in ('kind','source','sourceAssetId') if k in a.get('provenance',{})};used.append(proof)
  return '<img alt="'+esc(slot)+'" src="data:'+mime+';base64,'+base64.b64encode(b).decode()+'">'
 title=localized(spec.get('title'),lang) or chapter;captions.append(title)
 pages=['<section class="page cover"><h1>'+esc(title)+'</h1><div class="art">'+image(cover_asset or spec.get('coverAssetId'),'cover')+'</div><p>Unpublished draft · '+esc(chapter)+' · v'+str(version)+'</p></section>']
 for i,p in enumerate(panels):
  caption_value=p.get('captions',p.get('caption'));text=localized(caption_value,lang)
  if not text and isinstance(caption_value,dict):missing.append({'slot':p['id'],'reason':'caption-language-missing','language':lang})
  if len(text)>12000:raise ValueError('Caption too long; no silent truncation')
  if text:captions.append(text)
  pages.append('<section class="page"><h2>'+str(i+1)+'. '+esc(p['id'])+'</h2><div class="art">'+image(p.get('imageAssetId'),p['id'])+'</div><p class="caption">'+esc(text).replace('\n','<br>')+'</p></section>')
 for i in range(3):
  identifier=coloring[i] if i<len(coloring) else None
  if identifier in assets and assets[identifier].get('provenance',{}).get('kind') not in ('line-art','coloring-page','provided-line-art'):raise ValueError('Coloring art must be explicitly registered as supplied line art')
  label='Coloring page '+str(i+1)
  pages.append('<section class="page"><h2>'+label+'</h2><p>'+('Provided line art; source identity retained.' if identifier else 'Line art not provided. This is a reserved slot, not a generated coloring page.')+'</p><div class="art">'+image(identifier,'coloring-'+str(i+1))+'</div></section>')
 css='''@page{size:A4 landscape;margin:12mm}@page cover{size:A4 portrait;margin:12mm}*{box-sizing:border-box}body{margin:0;color:#27251f;font-family:Arial,sans-serif}.page{width:273mm;height:186mm;display:flex;flex-direction:column;break-after:page;break-inside:avoid}.page:last-child{break-after:auto}.cover{page:cover;width:186mm;height:273mm}h1,h2{margin:0 0 4mm}.art{flex:1;min-height:0;display:flex;align-items:center;justify-content:center}.art img{width:100%;height:100%;object-fit:contain}.missing{border:1px dashed #888;padding:12mm;color:#555}.caption{font-size:17pt;line-height:1.35;white-space:normal}p{margin:4mm 0 0}'''
 content='<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8"><title>'+esc(title)+'</title><style>'+css+'</style></head><body>'+''.join(pages)+'</body></html>'
 metadata={'schemaVersion':1,'unpublished':True,'productionApprovalInferred':False,'chapterId':chapter,'version':version,'sourceRecordSHA256':record_sha,'sourceVersionSHA256':record.get('sha256'),'sourceReferenceHash':record.get('referenceHash'),'savedReferenceBindingVerified':record.get('referenceHash') is not None,'language':lang,'pageCount':len(pages),'panelOrder':ids,'coloringSlotCount':3,'missingArtwork':missing,'selectedArtwork':used,'requiredSelectableText':captions,'originalAssetsModified':False,'generationCalls':0,'paidUSD':0,'selection':{'coverAssetId':cover_asset or spec.get('coverAssetId'),'coloringAssetIds':list(coloring)},'embeddedArtworkBytes':embedded_bytes,'maxEmbeddedArtworkBytes':max_embedded_bytes}
 out.mkdir(parents=True,exist_ok=True);b=content.encode();(out/'preview.html').write_bytes(b);metadata['html']={'file':'preview.html','sha256':digest(b),'bytes':len(b)};(out/'delivery-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');return metadata

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--record',required=True);p.add_argument('--record-sha256',required=True);p.add_argument('--chapter',required=True);p.add_argument('--version',type=int,required=True);p.add_argument('--registry',required=True);p.add_argument('--asset-root',required=True);p.add_argument('--out',required=True);p.add_argument('--language',choices=['en','ru'],default='en');p.add_argument('--cover-asset',help='Explicit selected registered cover/title reference. No implicit fallback.');p.add_argument('--max-embedded-bytes',type=int,default=256*1024*1024);p.add_argument('--coloring-asset',action='append',default=[],help='Explicit provided line-art asset ID, up to3. No automatic conversion.');a=p.parse_args();registry=json.loads(Path(a.registry).read_text());print(json.dumps(prepare(a.record,a.record_sha256,a.chapter,a.version,registry.get('assets',[]) if isinstance(registry,dict) else registry,a.asset_root,a.out,a.language,a.coloring_asset,a.cover_asset,a.max_embedded_bytes),ensure_ascii=False))
if __name__=='__main__':main()
