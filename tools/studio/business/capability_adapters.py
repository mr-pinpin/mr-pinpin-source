"""Reloadable example registration. No production code runs at import/descriptor time."""
import time
from model import StudioError, find, valid_id
from review_state import state_at_revision
from . import chapter_drafts
from .draft_pdf_delivery import chunk

def obj(fields,required): return {'type':'object','fields':fields,'required':required}
def ident(): return {'type':'id','maxLength':160}
def text(length): return {'type':'text','maxLength':length}
def num(lo,hi): return {'type':'integer','minimum':lo,'maximum':hi}
def descriptor(identifier,effect,fields,required,request=32768,response=1024*1024):
    return {'id':identifier,'effect':effect,'method':'POST','request':obj(fields,required),
            'maxRequestBytes':request,'maxResponseBytes':response,'timeoutMs':10000}

def business_capabilities():
    fields={k:text(1500) for k in ('action','cause','effect','caption','camera')}
    fields.update(beat={'type':'enum','values':['setup','repeat','turn','payoff']},seconds=num(1,120),
                  castIds={'type':'array','maxItems':16,'items':ident()},
                  dependsOn={'type':'array','maxItems':512,'items':ident()},
                  previewKind={'type':'enum','values':['schematic-placeholder','reused-reference','generated']},
                  imageAssetId=ident())
    patch={'chapterId':ident(),'baseVersion':num(1,100),'baseSHA256':{'type':'hash'},'expectedRevision':num(0,9007199254740991),
           'patches':{'type':'array','maxItems':12,'items':obj({'panelId':ident(),'fields':obj(fields,[])},['panelId','fields'])},
           'request':text(16000),'reason':text(500)}
    authorize={'chapterId':ident(),'version':num(1,100),'sha256':{'type':'hash'},'referenceHash':{'type':'hash'},
               'expectedRevision':num(0,9007199254740991),'explicitFullProductionGo':{'type':'boolean'},'userInstruction':text(4000)}
    pdf={'chapterId':ident(),'version':num(1,100),'sourceVersionSHA256':{'type':'hash'},'artifactSHA256':{'type':'hash'},
         'language':{'type':'enum','values':['en','ru']},'offset':num(0,67108864)}
    return [descriptor('draft.get.v1','read',{'chapterId':ident(),'page':num(0,42)},['chapterId']),
            descriptor('draft.patch.v1','mutation',patch,['chapterId','baseVersion','baseSHA256','expectedRevision','patches']),
            descriptor('draft.authorize.v1','mutation',authorize,list(authorize)),
            descriptor('draft.pdf.chunk.v1','read',pdf,list(pdf),4096,98304)]

def business_dispatch(store,operation,body,context):
    if time.monotonic() >= context['deadlineMonotonic']:
        raise StudioError('Business deadline expired; do not replay','business_timeout',504)
    if operation=='draft.get.v1':
        state=state_at_revision(store,context['revision'] if context['readOnly'] else None)
        chapter=find(state['project']['chapters'],valid_id(body['chapterId']),'chapter')
        draft=chapter_drafts.draft_context(chapter,page=body.get('page',0),store=store,state=state)
        if draft:
            draft['patchRoute']='/api/business/draft.patch.v1'
            draft['authorizeRoute']='/api/business/draft.authorize.v1'
        return {'draft':draft,'revision':state['revision'],'readOnly':bool(state.get('readOnly'))}
    if operation=='draft.pdf.chunk.v1': return chunk(store,body)
    if context['readOnly']: raise StudioError('Historical views cannot mutate','read_only',403)
    if body.get('expectedRevision') != context['revision']:
        raise StudioError('Workspace revision differs; hydrate before mutation','revision_conflict',409)
    if operation=='draft.patch.v1': return chapter_drafts.patch_draft(store,body)
    if operation=='draft.authorize.v1': return chapter_drafts.authorize_production(store,body)
    raise StudioError('Unknown registered operation','not_found',404)
