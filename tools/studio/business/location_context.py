"""Bounded selected-location preparation guide; metadata never proves byte readiness."""
import json,hashlib
ROLES=['seamless-panorama','location-identity','book-style','geometry-underlay']
def prepare_schema():
    sha={'type':'string','pattern':'^[a-f0-9]{64}$'}
    return {'type':'object','additionalProperties':False,'required':['location','expectedRevision','request','prompt','references','camera','formatReview'],'properties':{
        'location':{'type':'string','minLength':1,'maxLength':160},'expectedRevision':{'type':'integer','minimum':0},
        'request':{'type':'string','minLength':1,'maxUTF8Bytes':32000},'prompt':{'type':'string','minLength':1,'maxUTF8Bytes':32000},
        'references':{'type':'array','minItems':3,'maxItems':5,'items':{'type':'object','additionalProperties':False,'required':['assetId','sha256','role'],'properties':{'assetId':{'type':'string','minLength':1},'sha256':sha,'role':{'enum':ROLES}}}},
        'camera':{'type':'object','additionalProperties':False,'required':['intention'],'properties':{'intention':{'type':'string','minLength':1},'eyeHeightIntent':{'type':'string'},'yawDegrees':{'type':'number','minimum':-360,'maximum':360},'pitchDegrees':{'type':'number','minimum':-90,'maximum':90},'fovDegrees':{'type':'number','minimum':1,'maximum':179}}},
        'formatReview':{'type':'object','additionalProperties':False,'required':['assetId','sha256','projection','seam','poles','evidence'],'properties':{'assetId':{'type':'string','minLength':1},'sha256':sha,'projection':{'enum':['pass']},'seam':{'enum':['pass']},'poles':{'enum':['pass']},'evidence':{'type':'string','minLength':1}}}}}

def bounded(value,limit=2048):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,default=str).encode()
    return value if len(raw)<=limit else {'omittedFromContext':True,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def location_context(store,location=None,selected_references=None):
    """selected_references optional trusted explicit role -> registered asset ID.
    Does not search other locations or infer a healthy reference from approval.
    """
    state=store.read();revision=state['revision']
    result={'workflow':'workflows/location-creation.md','helper':'tools/studio-python tools/location_ops.py','projectRevision':revision,'generationDispatched':False,'referenceRoles':{'seamless-panorama':'Reviewed healthy projection/finish exemplar; never inherit its room layout','location-identity':'Actual selected location illustration/landmarks','book-style':'Visual style only; may share target bytes under explicit separate role','geometry-underlay':'Optional measured geometry; never required or relabeled panorama'},'commands':['context --location EXACT_ID','prepare ENVELOPE.json'],'availability':'Catalog metadata is not proof of bytes; prepare verifies registered local identities or returns pending-restore','next':'Select/inspect actual references, retain literal request/prompt and camera; prepare one native request only','schemaKind':'Authoring schema plus cross-field rules; not an independent validator; maxUTF8Bytes is a descriptive extension','prepareSchema':prepare_schema(),'crossFieldRules':['Require all first three roles; geometry optional','Format asset ID differs from target identity','Style may share target bytes with a separate book-style role','Unique assetId/role pair, three to five bindings','Target SHA must occur in selected catalog','Format review ID/SHA matches panorama input; all checks pass with actual observed evidence','Finite degree values and nonblank prompt/request/camera intention','Total request <=131072 UTF8 bytes; expectedRevision current at preparation']}
    bindings={}
    selection_rows=[]
    if location:
        from .location_workflow import catalog
        value=catalog(store,location)
        for row in value.get('media',[])[:12]:
            digest=row.get('sha256');asset=next((a for a in state['assets'] if a.get('sha256')==digest),None)
            selection_rows.append({'path':str(row.get('path',''))[:400],'sha256':digest,'bytes':row.get('bytes'),'roles':[str(x)[:80] for x in row.get('roles',[])[:8]],'catalogApprovalEvidence':bounded(row.get('approval'),256),'availability':'metadata-only','registeredAssetId':asset['id'] if asset else None})
        result['selection']={'location':bounded(value.get('location'),1024),'requestedSelector':location,'indexProvenance':bounded(value.get('indexProvenance')),'references':selection_rows,'truncated':len(value.get('media',[]))>12}
    for role,identifier in (selected_references or {}).items():
        if role not in ROLES:continue
        asset=next((a for a in state['assets'] if a['id']==identifier),None)
        if asset:
            bindings[role]={'assetId':asset['id'],'sha256':asset['sha256'],'role':role}
    def binding(role):return bindings.get(role,{'assetId':'SELECT_'+role.upper().replace('-','_')+'_ASSET_ID','sha256':'REPLACE_WITH_EXACT_REGISTERED_SHA256','role':role})
    references=[binding(role) for role in ROLES[:3]]
    result['prepareEnvelopeTemplate']={'location':location or 'SELECT_EXISTING_EXACT_LOCATION_ID','expectedRevision':revision,'request':'REPLACE_WITH_LITERAL_USER_REQUEST','prompt':'REPLACE_WITH_EXACT_SUBMITTED_PROMPT','references':references,'camera':{'intention':'REPLACE_WITH_USER_CAMERA_INTENTION','yawDegrees':0,'pitchDegrees':0,'fovDegrees':90},'formatReview':{'assetId':references[0]['assetId'],'sha256':references[0]['sha256'],'projection':'pass','seam':'pass','poles':'pass','evidence':'REPLACE_WITH_ACTUAL_VIEWER_OBSERVATIONS_NOT_CATALOG_APPROVAL'}}
    result['templateStatus']='requires actual reference selection, camera intention, prompt and visual review; never submit placeholders'
    result['provenanceExample']={'source':'location-workflow-proposal','status':'proposed-variant-unreviewed','originalLocationUnchanged':True,'derivedFrom':'selected catalog + exact registered reference identities','preparedArtifacts':['reports/location-workflow/CONTENT_HASH/prompt.txt','reports/location-workflow/CONTENT_HASH/prepared.json'],'sourceRolesRetained':True,'generationDispatched':False,'actualByteAvailability':'determined only during prepare; absent -> pending-restore'}
    result['selectionExample']={'seamless-panorama':'existing healthy panorama viewed across rear wrap/poles; role is format only','location-identity':'selected target illustration registered after existing scoped hydration','book-style':'explicit target/style input, separate role even if same target bytes','geometry-underlay':'optional existing Blender underlay only when user asks measured geometry'}
    # Fixed bound regardless of catalog provenance/metadata. Never dump all locations.
    if len(json.dumps(result,ensure_ascii=False).encode())>24576:
        result['selection']=dict(result.get('selection',{}),references=[],metadataOmittedForContextBound=True)
    return result
