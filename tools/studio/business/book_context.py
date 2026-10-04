"""Bounded saved-plan projection; never inject immutable history into a turn."""
def planning_context(project,chapter_id=None,scene_ids=(),revision=None):
    saved=project.get('book',{}).get('studioBookPlan')
    if not saved or not saved.get('versions'):return {'ready':False,'projectRevision':revision,'workflow':workflow_context(project,chapter_id,revision)}
    version=next((v for v in saved['versions'] if v['version']==saved['currentVersion']),None)
    if not version:return None
    spec=version['spec'];all_moments=spec.get('moments',[])
    chapter=[m for m in all_moments if not chapter_id or m['chapterId']==chapter_id]
    matched=[m for m in chapter if set(m.get('shotIds',[])) & set(scene_ids)]
    selected=(matched or chapter)[:8]
    def moment(m):
        return {'id':m['id'],'chapterId':m['chapterId'],'intent':m.get('intent','')[:240],
          'category':m.get('category'),'estimatedSeconds':m.get('estimatedSeconds'),
          'castIds':m.get('castIds',[])[:8],'dependsOn':m.get('dependsOn',[])[:8],
          'sequenceId':m.get('sequenceId'),'interactionIntent':m.get('interactionIntent','')[:120]}
    overview=[moment(all_moments[round(i*(len(all_moments)-1)/(min(8,len(all_moments))-1))]) for i in range(min(8,len(all_moments)))] if len(all_moments)>1 else [moment(m) for m in all_moments]
    ids={m['id'] for m in selected}
    links=[{'id':l.get('id'),'from':l['from'],'to':l['to'],'kind':l['kind'],'resolved':l.get('resolved',False)} for l in spec.get('links',[]) if l['from'] in ids or l['to'] in ids][:12]
    return {'ready':True,'workflow':workflow_context(project,chapter_id,revision),'version':version['version'],'sha256':version['sha256'],'projectRevision':revision,
      'brief':spec.get('brief','')[:800],'arc':spec.get('arc','')[:600],
      'chapterIntent':next((i.get('intent','')[:600] for i in spec.get('chapterIntents',[]) if i['chapterId']==chapter_id),None),
      'overview':overview,'selectedMoments':list(map(moment,selected)),'links':links,
      'totalMoments':len(all_moments),'selectedChapterMomentCount':len(chapter),
      'referenceBindings':version.get('referenceBindings',[])[:8],'projection':'bounded editorial context; full intent/DAG remains saved',
      'retrieval':{'command':'tools/studio-python tools/book_plan_ops.py context','operation':'book.get.v1','chapterId':chapter_id,'page':0,'version':version['version'],'guidePath':'workflows/book-planning.md'},
      'revisionWorkflow':'Use the helper context then one guarded patch call; retain literal user intent and saved tempo/DAG. Do not explore whole thread. Full production requires separate chapter go.'}

def workflow_context(project,chapter_id=None,revision=None):
    """Always available first-plan hint, independent of existing plan hydration."""
    saved=project.get('book',{}).get('studioBookPlan',{})
    current=next((v for v in saved.get('versions',[]) if v['version']==saved.get('currentVersion')),None)
    prefix='tools/studio-python tools/book_plan_ops.py'
    chapter_ids=[c['id'] for c in project.get('chapters',[]) if not chapter_id or c['id']==chapter_id][:12]
    return {'guidePath':'workflows/book-planning.md','helper':prefix,
      'configuration':'Host-provided PINPIN_STUDIO_DATA and PINPIN_STUDIO_RUNTIME, or explicit --data-dir/--runtime-dir; never guess a deployment',
      'context':prefix+' context'+(' --chapter '+chapter_id if chapter_id else ''),
      'save':prefix+' save <book-plan-envelope.json>',
      'patch':prefix+" patch --moment <actualMomentId> --version <currentVersion> --sha256 <currentSHA256> --expected-revision <projectRevision> --fields '<changed-fields JSON>' --request '<literal user revision>'",
      'guards':{'baseVersion':current['version'] if current else 0,'baseSHA256':current['sha256'] if current else None,'expectedRevision':revision},
      'actualChapterIds':chapter_ids,'ready':bool(current),
      'minimalSaveSchema':{'requiredEnvelope':['spec','request','expectedRevision','baseVersion'],'existingPlanAlsoRequires':['baseSHA256'],'specRequired':['brief','arc','moments'],'momentRequired':['id','chapterId','intent','category'],'categories':['setup','repetition','reaction','pause','turn','payoff'],'momentOptional':{'estimatedSeconds':'number >0 and <=3600; editorial estimate, never measured','castIds':'existing character entity IDs only','shotIds':'existing chapter.scenes IDs only; draft panel IDs are not scene IDs','dependsOn':'earlier known moment IDs, acyclic','sequenceId':'valid logical ID','interactionIntent':'literal supplied intent'},'linkRequired':['id','from','to','kind','resolved','explanation'],'linkKinds':['cause-effect','setup-payoff'],'resolved':'boolean; true endpoints must exist; setup-payoff requires matching setup/payoff categories','optionalSpec':['chapterIntents','links','referenceIds','intendedTargetSeconds'],'limits':{'moments':4096,'references':64,'briefBytes':16000,'arcBytes':16000,'momentIntentBytes':4000},'omitUnsupportedFields':True},
      'minimalSaveExample':{'request':'<literal user request>','expectedRevision':revision,'baseVersion':current['version'] if current else 0,**({'baseSHA256':current['sha256']} if current else {}),'spec':{'brief':'<literal user brief>','arc':'','chapterIntents':[],'moments':[{'id':'moment-1','chapterId':chapter_ids[0] if chapter_ids else '<choose actual chapter>','intent':'<beat derived from saved chapter or user words>','category':'setup','estimatedSeconds':5,'castIds':[],'shotIds':[],'dependsOn':[]}],'links':[],'referenceIds':[]}},
      'selectedDraftBinding':next(({'chapterId':c['id'],'version':c['studioDraft']['currentVersion'],'sha256':next((v['sha256'] for v in c['studioDraft'].get('versions',[]) if v['version']==c['studioDraft']['currentVersion']),None)} for c in project.get('chapters',[]) if c['id']==chapter_id and c.get('studioDraft')),None),
      'schemaUsage':'Fill this envelope directly; no source lookup is needed. Replace example prose with literal user intent/actual saved beats. Arc remains empty unless supplied. Do not alter chapter draft bindings or invent source IDs.',

      'saveEnvelope':'{spec:{brief,arc,chapterIntents,moments,links,referenceIds},request:<literal user words>,expectedRevision,baseVersion,baseSHA256 if existing}',
      'firstPlan':'Persist the user-declared book intent/DAG/estimated tempo using actual chapters. Show coarse8–12 moments; do not invent a story or invoke providers.',
      'production':'Planning save/patch grants no production authority. Separate explicit chapter go remains required.'}


def cli_book_route(store,method,path,query,body):
    """Fixed reloadable routes for the existing active-bundle CLI invoke contract."""
    operations={'/api/book-plans/context':('GET','book.get.v1'),'/api/book-plans/save':('POST','book.save.v1'),'/api/book-plans/patch':('POST','book.patch.v1')}
    if path not in operations:return None
    from model import StudioError
    from review_state import state_at_revision
    from business_contract import value_valid,bounded_json
    from . import book_capabilities
    import time
    required_method,operation=operations[path]
    if method!=required_method:raise StudioError('Book operation method differs','invalid_request',405)
    query=query or {};historical=False;revision=None
    if method=='GET':
        if set(query)-{'chapterId','sequenceId','momentId','page','version','revision'}:raise StudioError('Unknown context selector','business_contract',400)
        payload={}
        for key,values in query.items():
            if not isinstance(values,list) or len(values)!=1 or not isinstance(values[0],str):raise StudioError('Invalid context selector','business_contract',400)
            if key in ('page','version','revision'):
                try:value=int(values[0])
                except ValueError:raise StudioError('Invalid numeric selector','business_contract',400)
            else:value=values[0]
            if key=='revision':revision=value;historical=True
            else:payload[key]=value
        state=state_at_revision(store,revision)
    else:
        if query:raise StudioError('Mutation query selectors forbidden','business_contract',400)
        payload=body;state=store.read()
    descriptor=next(d for d in book_capabilities.business_capabilities() if d['id']==operation)
    if not value_valid(descriptor['request'],payload):raise StudioError('Guarded bounded book request required','business_contract',400)
    bounded_json(payload,descriptor['maxRequestBytes'])
    context={'readOnly':bool(historical or state.get('readOnly')),'revision':state['revision'],'deadlineMonotonic':time.monotonic()+10}
    result=book_capabilities.business_dispatch(store,operation,payload,context)
    if method=='GET':result['workflow']=workflow_context(state['project'],payload.get('chapterId'),state['revision'])
    return 200,result
