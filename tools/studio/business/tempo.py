"""Editorial estimated rhythm from a saved declarative plan; never reading measurement."""
from .book_plans import CATEGORIES,current,overview_indices
from model import StudioError

def tempo_summary(project,chapter_id=None,sequence_id=None,version=None):
    v=current(project) if version is None else next((x for x in project.get('book',{}).get('studioBookPlan',{}).get('versions',[]) if x['version']==version),None)
    if not v:return {'ready':False,'measurement':'none','estimatedTotalSeconds':None}
    moments=[m for m in v['spec']['moments'] if (chapter_id is None or m['chapterId']==chapter_id) and (sequence_id is None or m.get('sequenceId')==sequence_id)]
    known=sum(m['estimatedSeconds'] for m in moments if m.get('estimatedSeconds') is not None);missing=sum(m.get('estimatedSeconds') is None for m in moments)
    categories={k:{'moments':0,'knownEstimatedSeconds':0,'unknownMoments':0} for k in CATEGORIES};cast={}
    for m in moments:
        bucket=categories[m['category']];bucket['moments']+=1
        if m.get('estimatedSeconds') is None:bucket['unknownMoments']+=1
        else:bucket['knownEstimatedSeconds']+=m['estimatedSeconds']
        for entity in m.get('castIds',[]):cast[entity]=cast.get(entity,0)+1
    ids={m['id'] for m in moments};links=v['spec'].get('links',[])
    related=[l for l in links if l['from'] in ids or l['to'] in ids]
    # Chart uses at most120 aggregate bins, not thousands of DOM bars.
    bins=[];width=max(1,(len(moments)+119)//120)
    for start in range(0,len(moments),width):
        group=moments[start:start+width];unknown=sum(m.get('estimatedSeconds') is None for m in group)
        bins.append({'firstMomentId':group[0]['id'],'lastMomentId':group[-1]['id'],'momentCount':len(group),'estimatedSeconds':None if unknown else sum(m['estimatedSeconds'] for m in group),'knownEstimatedSeconds':sum(m['estimatedSeconds'] for m in group if m.get('estimatedSeconds') is not None),'unknownMoments':unknown,'categories':{k:sum(m['category']==k for m in group) for k in CATEGORIES}})
    target=v['spec'].get('intendedTargetSeconds')
    return {'ready':True,'bookPlanVersion':v['version'],'bookPlanSHA256':v['sha256'],'measurement':'editorial estimate from saved plan; not measured child reading or studio ground truth','estimatedTotalSeconds':None if missing else known,'knownEstimatedSeconds':known,'unknownMoments':missing,'momentCount':len(moments),'categories':categories,'bins':bins,'intendedTarget':None if target is None else {'seconds':target,'label':'user editorial heuristic for whole book; not measured or industry ground truth'},'castParticipation':[{'entityId':entity,'plannedMomentCount':count} for entity,count in sorted(cast.items())],'castCaveat':'Participation does not prove interaction; explicit interactionIntent is planned intent only.','unresolvedLinks':[l for l in related if not l['resolved']][:24],'unresolvedLinkCount':sum(not l['resolved'] for l in related),'setupPayoffCount':sum(l['kind']=='setup-payoff' and l['resolved'] for l in related),'timing':{'requestAcceptanceToCompletionSeconds':None}}
