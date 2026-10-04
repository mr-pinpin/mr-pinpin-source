"""Additive named planning operations. No I/O during registration."""
import copy,json,time
from model import StudioError
from review_state import state_at_revision
from . import book_plans
from .capability_adapters import descriptor,ident,text,num

def business_capabilities():
    selectors={'page':num(0,341),'chapterId':ident(),'sequenceId':ident(),'momentId':ident(),'version':num(1,100)}
    guards={'expectedRevision':num(0,9007199254740991),'baseVersion':num(0,100),'baseSHA256':{'type':'hash'},'request':text(16000)}
    chunks={'type':'array','maxItems':48,'items':text(16000)}
    return [descriptor('book.get.v1','read',selectors,[]),
      descriptor('book.save.v1','mutation',dict(guards,specChunks=chunks),['expectedRevision','baseVersion','request','specChunks'],request=1024*1024),
      descriptor('book.patch.v1','mutation',dict(guards,patchesJson=text(16000)),['expectedRevision','baseVersion','baseSHA256','request','patchesJson'],request=65536),
      descriptor('book.request.v1','read',{'kind':{'type':'enum','values':['expand-sequence','compact-comic-page']},'momentIds':{'type':'array','maxItems':12,'items':ident()},'baseVersion':num(1,100),'baseSHA256':{'type':'hash'}},['kind','momentIds','baseVersion','baseSHA256'])]

def decode(value):
    try:return json.loads(value,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    except (ValueError,RecursionError):raise StudioError('Invalid planning JSON','business_contract',400)

def business_dispatch(store,operation,body,context):
    if time.monotonic()>=context['deadlineMonotonic']:raise StudioError('Planning deadline expired','business_timeout',504)
    if operation=='book.get.v1':
        state=state_at_revision(store,context['revision'] if context['readOnly'] else None)
        mapping={'chapterId':'chapter_id','sequenceId':'sequence_id','momentId':'moment_id','page':'page','version':'version'}
        result=copy.deepcopy(book_plans.planning_view(state,**{mapping[k]:v for k,v in body.items()}))
        # Chapter intents are separately paged to retain bounded responses for long books.
        plan=result['plan']
        for moment in plan.get('moments',[])+plan.get('overview',[]):
            if 'shotIds' in moment:
                moment['shotIdCount']=len(moment['shotIds']);moment['shotIds']=moment['shotIds'][:24]
        intents=plan.get('chapterIntents',[]);page=body.get('page',0)
        plan['chapterIntentCount']=len(intents);plan['chapterIntentPage']=page
        plan['chapterIntents']=intents[page*12:(page+1)*12]
        return result
    if operation=='book.request.v1':
        if context['readOnly']:raise StudioError('Historical planning requests are read only','read_only',403)
        state=store.read();view=book_plans.view_plan(state['project'])
        if view.get('version')!=body['baseVersion'] or view.get('sha256')!=body['baseSHA256']:raise StudioError('Plan changed; refresh selection','revision_conflict',409)
        return book_plans.planning_request(state['project'],body['kind'],body['momentIds'])
    if operation not in ('book.save.v1','book.patch.v1'):raise StudioError('Unknown book operation','not_found',404)
    if context['readOnly']:raise StudioError('Historical plans are read only','read_only',403)
    if body['expectedRevision']!=context['revision']:raise StudioError('Workspace changed','revision_conflict',409)
    payload={k:v for k,v in body.items() if k not in ('specChunks','patchesJson')}
    if operation=='book.save.v1':
        payload['spec']=decode(''.join(body['specChunks']))
        return book_plans.save_plan(store,payload)
    payload['patches']=decode(body['patchesJson'])
    return book_plans.patch_plan(store,payload)
