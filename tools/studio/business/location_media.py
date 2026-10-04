"""Bounded local media-selection metadata. No media fetch/restore/generation."""
import hashlib,json,time
import media_library as archive
from model import StudioError
from .capability_adapters import descriptor,ident

def selection_metadata(media_id=None):
 root,entries=archive.media_entries();path=root/'location-manifest.json'
 if path.is_symlink() or not path.is_file():raise StudioError('Selected location viewer is not configured','location_not_ready',503)
 if path.stat().st_size>32768:raise StudioError('Location selection exceeds bound','location_manifest',413)
 raw=path.read_bytes()
 if len(raw)>32768:raise StudioError('Location selection exceeds bound','location_manifest',413)
 try:value=json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
 except (ValueError,RecursionError):raise StudioError('Invalid location selection','location_manifest',503)
 if not isinstance(value,dict) or value.get('schemaVersion')!=1 or not isinstance(value.get('stops'),list) or len(value['stops'])>24 or not isinstance(value.get('repairs',[]),list) or len(value.get('repairs',[]))>4:raise StudioError('Invalid bounded location selection','location_manifest',503)
 expected=value.get('sha256');unsigned={k:v for k,v in value.items() if k!='sha256'}
 actual=hashlib.sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if actual!=expected:raise StudioError('Location selection identity differs','storage_corruption',500)
 refs=[value.get('panorama'),value.get('orbit')]+[r.get('media') for r in value.get('repairs',[])]+[r.get(key) for r in value['stops'] for key in ('panorama','sourceFrame')]
 registered={}
 for ref in refs:
  if ref is None:continue
  if not isinstance(ref,dict) or set(ref)!={'id','sha256'}:raise StudioError('Invalid media reference','location_manifest',503)
  row=entries.get(ref['id'])
  if not row or row['sha256']!=ref['sha256'] or 'bytes' not in row:raise StudioError('Selection media identity unavailable','location_manifest',503)
  registered[ref['id']]={key:row.get(key) for key in ('mime','sha256','bytes','reviewStatus','projection','name')}
 if media_id and media_id not in registered and media_id!=value.get('id'):raise StudioError('Selected media not found','not_found',404)
 return {'manifest':value,'registry':registered,'selectionId':value['id'],'mediaBytesVerified':False,'verification':'Registry bindings only; media route verifies actual SHA/size/type on read'}

def business_capabilities():
 return [descriptor('spaces.location.get.v1','read',{'mediaId':ident()},['mediaId'],response=65536)]

def business_dispatch(store,operation,body,context):
 if operation!='spaces.location.get.v1':raise StudioError('Unknown location media operation','not_found',404)
 if time.monotonic()>=context['deadlineMonotonic']:raise StudioError('Location metadata deadline expired','business_timeout',504)
 if context['readOnly']:raise StudioError('Current local media selection is not historical evidence','read_only',403)
 return selection_metadata(body['mediaId'])
