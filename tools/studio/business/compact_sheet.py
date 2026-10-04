"""Page-level compact previews; independent of draft/reference/approval core.
No artwork registration or generation. Prompt/receipt digest assertions are labeled;
source version/order and registered local asset bytes are independently verified.
"""
import copy,json,re
from model import StudioError,find,valid_id,now
from review_state import state_at_revision
from .capability_adapters import descriptor,ident,num
from .chapter_drafts import local_verified

MAX_SHEETS=32

def business_capabilities():
 fields={'chapterId':ident(),'sourceVersion':num(1,100),'sourceVersionSHA256':{'type':'hash'},'assetId':ident(),'assetSHA256':{'type':'hash'},'panelIds':{'type':'array','maxItems':512,'items':ident()},'columns':num(1,16),'rows':num(1,32),'promptSHA256':{'type':'hash'},'receiptSHA256':{'type':'hash'},'expectedRevision':num(0,9007199254740991)}
 return [descriptor('draft.sheet.bind.v1','mutation',fields,list(fields),131072,131072),descriptor('draft.sheet.get.v1','read',{'chapterId':ident()},['chapterId'],4096,1048576)]

def sheet_views(chapter,assets):
 draft=chapter.get('studioDraft',{});current=next((v for v in draft.get('versions',[]) if v['version']==draft.get('currentVersion')),None)
 assets={a['id']:a for a in assets};result=[]
 for record in chapter.get('studioDraftPreviews',[])[:MAX_SHEETS]:
  item=copy.deepcopy(record);asset=assets.get(item['assetId'])
  item['stale']=not current or item['sourceVersion']!=current['version'] or item['sourceVersionSHA256']!=current['sha256']
  item['registeredAssetMatches']=bool(asset and asset.get('sha256')==item['assetSHA256'])
  result.append(item)
 return result

def business_dispatch(store,operation,body,context):
 state=state_at_revision(store,context['revision'] if context['readOnly'] else None)
 chapter=find(state['project']['chapters'],valid_id(body['chapterId']),'chapter')
 if operation=='draft.sheet.get.v1':return {'sheets':sheet_views(chapter,state['assets']),'revision':state['revision'],'readOnly':bool(context['readOnly'])}
 if operation!='draft.sheet.bind.v1':raise StudioError('Unknown sheet operation','not_found',404)
 if context['readOnly']:raise StudioError('Historical views cannot bind previews','read_only',403)
 if body.get('expectedRevision')!=state['revision'] or context['revision']!=state['revision']:raise StudioError('Revision differs','revision_conflict',409)
 for key in ('sourceVersionSHA256','assetSHA256','promptSHA256','receiptSHA256'):
  if not isinstance(body.get(key),str) or not re.fullmatch('[a-f0-9]{64}',body[key]):raise StudioError('Invalid sheet digest')
 version=next((v for v in chapter.get('studioDraft',{}).get('versions',[]) if v['version']==body.get('sourceVersion')),None)
 if not version or version['sha256']!=body['sourceVersionSHA256']:raise StudioError('Source draft version/hash differs','revision_conflict',409)
 panel_ids=body.get('panelIds');ordered=[p['id'] for p in version['spec']['panels']]
 if not isinstance(panel_ids,list) or not panel_ids or len(panel_ids)>512 or len(set(panel_ids))!=len(panel_ids) or panel_ids!=[p for p in ordered if p in panel_ids]:raise StudioError('Sheet panel IDs must match source order without duplicates')
 columns,rows=body.get('columns'),body.get('rows')
 if type(columns)!=int or type(rows)!=int or not 1<=columns<=16 or not 1<=rows<=32 or columns*rows!=len(panel_ids):raise StudioError('Grid must account for exactly the bound panels')
 asset=find(state['assets'],valid_id(body['assetId']),'asset')
 if asset.get('sha256')!=body['assetSHA256'] or not str(asset.get('mime','')).startswith('image/') or not local_verified(store,state,asset):raise StudioError('Registered sheet bytes are unavailable or differ','sheet_asset_unverified',409)
 record={k:copy.deepcopy(body[k]) for k in ('sourceVersion','sourceVersionSHA256','assetId','assetSHA256','panelIds','columns','rows','promptSHA256','receiptSHA256')}
 record.update(kind='compact-sheet',boundAt=now(),assetVerifiedAtBinding=True,provenanceStatus='caller-declared-prompt-and-receipt-digests')
 existing=chapter.setdefault('studioDraftPreviews',[])
 if any(all(r.get(k)==record[k] for k in record if k!='boundAt') for r in existing):raise StudioError('Identical sheet binding already exists','unchanged',409)
 if len(existing)>=MAX_SHEETS or len(json.dumps(existing+[record],ensure_ascii=False).encode())>512*1024:raise StudioError('Compact preview history bound reached')
 existing.append(record);saved=store.save_project(state['project'],body['expectedRevision'])
 return {'sheet':record,'revision':saved['revision'],'artworkCreated':False,'productionAuthorized':False}
