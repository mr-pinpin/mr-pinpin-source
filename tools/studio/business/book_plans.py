"""Versioned declarative book/chapter planning. No generation or production authority."""
import copy,hashlib,json,time,re
from model import StudioError,valid_id,now
MAX_MOMENTS=4096
MAX_PLAN_HISTORY_BYTES=8*1024*1024
def canonical_size(value,maximum):
    total=0
    for chunk in json.JSONEncoder(sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).iterencode(value):
        total+=len(chunk.encode())
        if total>maximum:raise StudioError("Book plan history exceeds 8 MiB; retain immutable history and start a separate explicit plan rather than silently dropping versions","book_plan_budget",413)
    return total
PAGE_SIZE=12
CATEGORIES=('setup','repetition','reaction','pause','turn','payoff')
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def bounded(value,name,limit,empty=False):
    if not isinstance(value,str) or (not empty and not value.strip()) or len(value.encode())>limit:raise StudioError('Invalid '+name)
def acyclic(nodes,edges):
    incoming={n:0 for n in nodes};adj={n:set() for n in nodes}
    for source,target in edges:
        if source==target:raise StudioError('Self dependency')
        if target not in adj[source]:adj[source].add(target);incoming[target]+=1
    ready=[n for n,d in incoming.items() if d==0];count=0
    while ready:
        n=ready.pop();count+=1
        for target in adj[n]:
            incoming[target]-=1
            if incoming[target]==0:ready.append(target)
    if count!=len(nodes):raise StudioError('Cyclic dependencies')
def validate(state,spec):
    if not isinstance(spec,dict) or len(json.dumps(spec).encode())>2*1024*1024:raise StudioError('Plan exceeds 2 MiB')
    bounded(spec.get('brief'),'user brief',16000);bounded(spec.get('arc'),'book arc',16000,True)
    chapters={c['id']:c for c in state['project']['chapters']};cast={e['id'] for e in state['project']['entities'] if e.get('kind')=='character'}
    intents=spec.get('chapterIntents',[])
    if not isinstance(intents,list) or len(intents)>512:raise StudioError('Invalid chapter intents')
    seen=set()
    for i in intents:
        if not isinstance(i,dict) or i.get('chapterId') not in chapters or i['chapterId'] in seen:raise StudioError('Chapter intent needs unique actual chapter ID')
        seen.add(i['chapterId']);bounded(i.get('intent'),'chapter intent',4000)
    moments=spec.get('moments')
    if not isinstance(moments,list) or not 1<=len(moments)<=MAX_MOMENTS:raise StudioError('Plan needs 1–4096 moments')
    nodes={};edges=[]
    for m in moments:
        if not isinstance(m,dict):raise StudioError('Moment must be an object')
        mid=valid_id(m.get('id'))
        if mid in nodes or m.get('chapterId') not in chapters:raise StudioError('Unique moment and actual chapter ID required')
        nodes[mid]=m;bounded(m.get('intent'),'moment intent',4000)
        if m.get('category') not in CATEGORIES:raise StudioError('Unknown rhythm category')
        seconds=m.get('estimatedSeconds')
        if seconds is not None and (type(seconds) not in (int,float) or not 0<seconds<=3600):raise StudioError('Invalid estimated seconds')
        if 'sequenceId' in m:valid_id(m['sequenceId'])
        participants=m.get('castIds',[])
        if not isinstance(participants,list) or len(participants)>32 or len(set(participants))!=len(participants) or any(p not in cast for p in participants):raise StudioError('Invalid planned cast')
        shots=m.get('shotIds',[]);known_shots={s['id'] for s in chapters[m['chapterId']].get('scenes',[])}
        if not isinstance(shots,list) or len(shots)>512 or len(set(shots))!=len(shots) or any(s not in known_shots for s in shots):raise StudioError('Shot references must be actual chapter scene IDs')
        span=m.get('shotSpan')
        if span is not None:
            if not isinstance(span,dict) or set(span)!={'firstSceneId','lastSceneId'}:raise StudioError('Invalid saved shot span')
            order={s['id']:i for i,s in enumerate(chapters[m['chapterId']].get('scenes',[]))}
            if span['firstSceneId'] not in order or span['lastSceneId'] not in order or order[span['firstSceneId']]>order[span['lastSceneId']]:raise StudioError('Shot span needs actual ordered chapter endpoints')
        if 'interactionIntent' in m:bounded(m['interactionIntent'],'intended interaction',1500)
        dependencies=m.get('dependsOn',[])
        if not isinstance(dependencies,list) or len(dependencies)>64 or len(set(dependencies))!=len(dependencies):raise StudioError('Invalid dependencies')
    for mid,m in nodes.items():
        for source in m.get('dependsOn',[]):
            if source not in nodes:raise StudioError('Unknown dependency; use explicit unresolved link instead')
            edges.append((source,mid))
    links=spec.get('links',[])
    if not isinstance(links,list) or len(links)>8192:raise StudioError('Invalid links')
    link_ids=set()
    for link in links:
        if not isinstance(link,dict):raise StudioError('Invalid link')
        identifier=valid_id(link.get('id'))
        if identifier in link_ids:raise StudioError('Duplicate link ID')
        link_ids.add(identifier);source=valid_id(link.get('from'));target=valid_id(link.get('to'))
        if link.get('kind') not in ('cause-effect','setup-payoff') or type(link.get('resolved'))!=bool:raise StudioError('Invalid link kind/status')
        bounded(link.get('explanation'),'link explanation',1500)
        if link['resolved']:
            if source not in nodes or target not in nodes:raise StudioError('Resolved link points to unknown moment')
            if link['kind']=='setup-payoff' and (nodes[source]['category']!='setup' or nodes[target]['category']!='payoff'):raise StudioError('Setup/payoff endpoints must match categories')
            edges.append((source,target))
    acyclic(nodes,edges)
    target=spec.get('intendedTargetSeconds')
    if target is not None and (type(target) not in (int,float) or not 0<target<=86400):raise StudioError('Invalid editorial target')
    refs=spec.get('referenceIds',[]);assets={a['id']:a for a in state['assets']}
    if not isinstance(refs,list) or len(refs)>64 or len(set(refs))!=len(refs) or any(r not in assets for r in refs):raise StudioError('Unknown reference ID')
    for identifier in refs:
        asset=assets[identifier]
        if asset.get('provenance') is not None and not isinstance(asset.get('provenance'),dict):raise StudioError('Reference provenance must be metadata')
        if not isinstance(asset.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',asset['sha256']) or type(asset.get('bytes'))!=int or asset['bytes']<0:raise StudioError('Reference lacks exact catalog hash/size')
    return [{'assetId':r,'sha256':assets[r]['sha256'],'bytes':assets[r]['bytes'],'role':(assets[r].get('provenance') or {}).get('role','unspecified'),'availability':'catalog-only-not-byte-verified'} for r in sorted(refs)]
def current(project):
    plan=project.get('book',{}).get('studioBookPlan',{})
    return next((v for v in plan.get('versions',[]) if v['version']==plan.get('currentVersion')),None)
def save_plan(store,body):
    started=time.monotonic()
    if not isinstance(body,dict) or type(body.get('expectedRevision'))!=int:raise StudioError('expectedRevision required')
    if body.get('readOnly') or body.get('reviewSnapshot') or body.get('revision') is not None:raise StudioError('Historical plan cannot mutate')
    state=store.read()
    if state.get('readOnly'):raise StudioError('Historical plan cannot mutate')
    project=state['project'];previous=current(project);history=project.get('book',{}).get('studioBookPlan',{}).get('versions',[])
    if type(body.get('baseVersion'))!=int or body['baseVersion']!=(previous['version'] if previous else 0) or (previous and body.get('baseSHA256')!=previous['sha256']):raise StudioError('Hydrated version/hash required')
    if len(history)>=100:raise StudioError('Plan version bound reached')
    spec=copy.deepcopy(body.get('spec'))
    try:bindings=validate(state,spec)
    except (KeyError,TypeError,ValueError) as e:raise StudioError('Malformed plan fields') from None
    request=body.get('request','');bounded(request,'original request',16000,True)
    version={'version':len(history)+1,'createdAt':now(),'spec':spec,'referenceBindings':bindings,'sha256':fingerprint({'spec':spec,'references':bindings}),'request':request,'requestSHA256':fingerprint(request),'generationCalls':0,'productionStarted':False,'provenance':{'source':'declarative-user-plan','claims':'planned intent; no generated content or measured reading'},'timing':{'businessPreparationSeconds':None,'requestAcceptanceToCompletionSeconds':None}}
    if previous and version['sha256']==previous['sha256']:raise StudioError('Plan inputs are unchanged; reuse the current version instead of duplicating history','book_plan_unchanged',409)
    version['timing']['businessPreparationSeconds']=time.monotonic()-started
    candidate={'schemaVersion':1,'currentVersion':version['version'],'versions':history+[version],'production':'requires-separate-specific-chapter-go'}
    canonical_size(candidate,MAX_PLAN_HISTORY_BYTES)
    project['book']['studioBookPlan']=candidate
    saved=store.save_project(project,body['expectedRevision'])
    return {'version':version['version'],'sha256':version['sha256'],'revision':saved['revision'],'timing':version['timing'],'productionStarted':False}
def overview_indices(count,limit=10):
    if type(limit)!=int or not 8<=limit<=12:raise StudioError('Overview limit must be8–12')
    if count<=limit:return list(range(count))
    return [i*(count-1)//(limit-1) for i in range(limit)]
def view_plan(project,page=0,chapter_id=None,sequence_id=None,version=None,moment_id=None):
    if type(page)!=int or page<0:raise StudioError('Invalid page')
    plan=project.get('book',{}).get('studioBookPlan',{});v=current(project) if version is None else next((x for x in plan.get('versions',[]) if x['version']==version),None)
    if not v:return {'ready':False,'productionStarted':False}
    moments=v['spec']['moments'];selected=[m for m in moments if (chapter_id is None or m['chapterId']==chapter_id) and (sequence_id is None or m.get('sequenceId')==sequence_id)]
    if moment_id is not None:
        index=next((i for i,m in enumerate(selected) if m['id']==moment_id),None)
        if index is None:raise StudioError('Unknown selected moment')
        page=index//PAGE_SIZE
    pages=max(1,(len(selected)+PAGE_SIZE-1)//PAGE_SIZE)
    if page>=pages:raise StudioError('Page beyond selected sequence')
    return {'ready':True,'version':v['version'],'sha256':v['sha256'],'currentVersion':plan['currentVersion'],'historical':v['version']!=plan['currentVersion'],'selectedChapterId':chapter_id,'selectedSequenceId':sequence_id,'history':[{'version':x['version'],'sha256':x['sha256'],'createdAt':x['createdAt']} for x in plan['versions'][-10:]],'brief':v['spec']['brief'],'arc':v['spec']['arc'],'chapterIntents':v['spec'].get('chapterIntents',[]),'overview':[selected[i] for i in overview_indices(len(selected))],'overviewBasis':'deterministic evenly spaced representative moments; editable editorial selection, not quality judgement','moments':selected[page*PAGE_SIZE:(page+1)*PAGE_SIZE],'totalMoments':len(selected),'page':page,'pages':pages,'pageSize':PAGE_SIZE,'links':[l for l in v['spec'].get('links',[]) if l['from'] in {m['id'] for m in selected[page*PAGE_SIZE:(page+1)*PAGE_SIZE]} or l['to'] in {m['id'] for m in selected[page*PAGE_SIZE:(page+1)*PAGE_SIZE]}][:24],'linkCount':len(v['spec'].get('links',[])),'referenceBindings':v['referenceBindings'],'production':'requires-separate-specific-chapter-go','timing':v['timing']}
def planning_request(project,kind,moment_ids):
    v=current(project)
    if not v or kind not in ('expand-sequence','compact-comic-page'):raise StudioError('Invalid planning request')
    if not isinstance(moment_ids,list) or not 1<=len(moment_ids)<=12 or len(set(moment_ids))!=len(moment_ids):raise StudioError('Select1–12 moments')
    known={m['id']:m for m in v['spec']['moments']}
    if any(mid not in known for mid in moment_ids):raise StudioError('Unknown moment')
    return {'kind':kind,'bookPlanVersion':v['version'],'bookPlanSHA256':v['sha256'],'momentIds':moment_ids,'chapterIds':sorted({known[mid]['chapterId'] for mid in moment_ids}),'scope':'rough-preproduction','status':'request-only','generationCalls':0,'productionStarted':False,'requiresRegisteredVisualArtifact':kind=='compact-comic-page','productionGate':'separate explicit go bound to current reviewed chapter draft'}

def patch_plan(store,body):
    if not isinstance(body,dict) or len(json.dumps(body).encode())>32768:raise StudioError('Invalid bounded patch')
    state=store.read();v=current(state['project'])
    if not v or body.get('baseVersion')!=v['version'] or body.get('baseSHA256')!=v['sha256']:raise StudioError('Current plan version/hash required')
    spec=copy.deepcopy(v['spec']);patches=body.get('patches',[])
    if not isinstance(patches,list) or not 1<=len(patches)<=12:raise StudioError('Patch1–12 moments')
    nodes={m['id']:m for m in spec['moments']};seen=set()
    for patch in patches:
        if not isinstance(patch,dict) or patch.get('momentId') not in nodes or patch['momentId'] in seen:raise StudioError('Unique saved moment required')
        seen.add(patch['momentId']);fields=patch.get('fields')
        if not isinstance(fields,dict) or not fields or not set(fields)<={'intent','category','estimatedSeconds','castIds','interactionIntent','dependsOn','shotIds'}:raise StudioError('Unsupported planning fields')
        nodes[patch['momentId']].update(copy.deepcopy(fields))
    return save_plan(store,{**body,'spec':spec})


def planning_view(state,**options):
    """Registry read adapter: one snapshot, same plan version for overview and tempo."""
    from .tempo import tempo_summary
    view=view_plan(state['project'],**options)
    view['projectRevision']=state['revision']
    return {'plan':view,'tempo':tempo_summary(state['project'],chapter_id=options.get('chapter_id'),sequence_id=options.get('sequence_id'),version=view.get('version')),'revision':state['revision'],'readOnly':bool(state.get('readOnly'))}
