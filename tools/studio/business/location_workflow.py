"""Prepare one native location candidate using existing catalog and resolved assets.
Never generates, restores remotely, approves, publishes or projects image bytes.
"""
import hashlib,json,re,time
from pathlib import Path
from model import StudioError,find
from store import atomic_json
from . import asset_storage

ROLES=('seamless-panorama','location-identity','book-style','geometry-underlay')
def fail(message,code='location_workflow',status=422):raise StudioError(message,code,status)
def compact(value,limit):
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()
    if len(raw)>limit:fail('Location request exceeds bound')
    return raw

def catalog(store,location):
    if not isinstance(location,str) or not 1<=len(location)<=160:fail('Choose exact existing location')
    service=getattr(store,'location_capability_service',None)
    if service is None:fail('Existing location service is not configured','location_not_ready',503)
    return service.query(location=location,deadline=time.monotonic()+9,probe_media=False,network=False)

def reference_status(store,state,ref):
    if not isinstance(ref,dict) or set(ref)-{'assetId','sha256','role'} or ref.get('role') not in ROLES:fail('Explicit supported reference role required')
    asset=find(state['assets'],ref.get('assetId'),'asset')
    if ref.get('sha256')!=asset.get('sha256'):fail('Reference identity changed','reference_conflict',409)
    # Check canonical locality before calling existing resolver: absence must never
    # enter its remote restoration branch during this bounded operation.
    cfg=asset_storage.policy(store)
    registered,path,entry=asset_storage.asset_entry(store,asset['id'],cfg)
    if not path.exists():return dict(ref,bytes=entry['bytes'],availability='pending-restore',restoreOperation='existing asset_storage.resolve / host storage job')
    # Reuse the resolved-asset layer's exact registry/path/hash primitives.
    # Its public resolve() may restore over network after a concurrent removal;
    # local-only verification deliberately cannot take that remote branch.
    asset_storage.identity(path,entry['bytes'],entry['sha256'])
    value={'sha256':entry['sha256'],'bytes':entry['bytes'],'nativePath':str(path)}
    if value.get('sha256')!=ref['sha256'] or value.get('bytes')!=entry['bytes']:fail('Resolved reference differs','reference_conflict',409)
    return dict(ref,bytes=value['bytes'],nativePath=value['nativePath'],availability='verified-local',reviewStatus=registered.get('reviewStatus','unreviewed'))

def prepare(store,body):
    if not isinstance(body,dict) or set(body)-{'location','expectedRevision','request','prompt','references','camera','formatReview'}:fail('Unsupported location preparation field')
    compact(body,131072)
    state=store.read()
    if type(body.get('expectedRevision')) is not int or body['expectedRevision']!=state['revision']:fail('Workspace changed','revision_conflict',409)
    for key in ('request','prompt'):
        if not isinstance(body.get(key),str) or not body[key].strip() or len(body[key].encode())>32000:fail('Exact user request and submitted prompt required')
    refs=body.get('references')
    if not isinstance(refs,list) or not 3<=len(refs)<=5:fail('Use three to five explicit role bindings')
    roles=[r.get('role') for r in refs if isinstance(r,dict)]
    if any(role not in roles for role in ROLES[:3]):fail('Separate panorama format, target identity and style bindings required')
    if len({(r.get('assetId'),r.get('role')) for r in refs if isinstance(r,dict)})!=len(refs):fail('Duplicate reference binding')
    format_ids={r['assetId'] for r in refs if r.get('role')=='seamless-panorama'}
    if format_ids & {r['assetId'] for r in refs if r.get('role')=='location-identity'}:fail('Format exemplar and target location must be distinct inputs')
    camera=body.get('camera')
    if not isinstance(camera,dict) or set(camera)-{'intention','yawDegrees','pitchDegrees','fovDegrees','eyeHeightIntent'} or not isinstance(camera.get('intention'),str) or not camera['intention'].strip():fail('Explicit camera intention required')
    for key,lo,hi in [('yawDegrees',-360,360),('pitchDegrees',-90,90),('fovDegrees',1,179)]:
        if key in camera and (type(camera[key]) not in (int,float) or not lo<=camera[key]<=hi):fail('Camera degrees out of bounds')
    review=body.get('formatReview')
    if not isinstance(review,dict) or set(review)!={'assetId','sha256','projection','seam','poles','evidence'} or any(review[k]!='pass' for k in ('projection','seam','poles')) or not isinstance(review['evidence'],str) or not review['evidence'].strip():fail('Healthy format reference requires explicit actual visual review evidence')
    if not any(r.get('role')=='seamless-panorama' and r.get('assetId')==review['assetId'] and r.get('sha256')==review['sha256'] for r in refs):fail('Format review must bind exact exemplar hash')
    selection=catalog(store,body['location'])
    resolved=[reference_status(store,state,r) for r in refs]
    # Target identity must originate from selected catalog bytes, not a supplied label.
    media=selection.get('media',[])
    for ref in refs:
        if ref['role']=='location-identity' and not any(row.get('sha256')==ref['sha256'] for row in media):fail('Target reference does not belong to selected location catalog')
    missing=[r for r in resolved if r['availability']!='verified-local']
    if missing:return {'status':'pending-restore','references':resolved,'generationDispatched':False,'projectRevision':state['revision']}
    if store.read()['revision']!=state['revision']:fail('Workspace changed during resolution','revision_conflict',409)
    identity=hashlib.sha256(compact(dict(body,resolvedReferences=resolved),262144)).hexdigest()
    folder='reports/location-workflow/'+identity+'/'
    prompt_path=asset_storage.inside(store,folder+'prompt.txt');prompt_path.parent.mkdir(parents=True,exist_ok=True)
    prompt_bytes=body['prompt'].encode()
    # Immutable content-addressed preparation; never overwrite existing bytes.
    try:
        with prompt_path.open('xb') as stream:stream.write(prompt_bytes)
    except FileExistsError:
        if prompt_path.read_bytes()!=prompt_bytes:fail('Existing prompt differs','reference_conflict',409)
    result={'schemaVersion':1,'attemptId':identity,'status':'prepared','location':body['location'],'projectRevision':state['revision'],'request':body['request'],'promptFile':folder+'prompt.txt','promptSHA256':hashlib.sha256(prompt_bytes).hexdigest(),'references':resolved,'camera':camera,'formatReview':review,'catalogProvenance':selection.get('indexProvenance'),'tool':'image_gen.imagegen','toolRequest':{'prompt':body['prompt'],'referenced_image_paths':list(dict.fromkeys(r['nativePath'] for r in resolved)),'transparent_background':False},'generationDispatched':False,'outputStatus':'candidate-unreviewed','reviewRequired':['actual 2:1 dimensions','rear wrap seam','poles','doors/openings','landmarks','camera/occlusion','oblique viewer angles'],'deriveWith':'tools/panoramas/project.py export --input REGISTERED_MASTER --output EXTERNAL_DIR --width 3072 --face-size 1024','projectionDoesNotProveVisualApproval':True}
    record=asset_storage.inside(store,folder+'prepared.json')
    if record.exists():
        if json.loads(record.read_text())!=result:fail('Existing preparation differs','reference_conflict',409)
    else:atomic_json(record,result)
    return result

def cli_location_route(store,method,path,query,body):
    if path not in ('/api/location-workflow/context','/api/location-workflow/prepare'):return None
    if path.endswith('/context') and method=='GET':
        from .location_context import location_context
        if set(query)-{'location'} or any(not isinstance(v,list) or len(v)!=1 for v in query.values()):fail('Invalid location selector')
        return 200,location_context(store,query.get('location',[None])[0])
    if path.endswith('/prepare') and method=='POST' and not query:return 200,prepare(store,body)
    fail('Unsupported method/query','invalid_request',400)
