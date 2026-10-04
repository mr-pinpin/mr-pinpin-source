"""Bounded saved-plan projection; never inject immutable history into a turn."""
def planning_context(project,chapter_id=None,scene_ids=(),revision=None):
    saved=project.get('book',{}).get('studioBookPlan')
    if not saved or not saved.get('versions'):return None
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
    return {'version':version['version'],'sha256':version['sha256'],'projectRevision':revision,
      'brief':spec.get('brief','')[:800],'arc':spec.get('arc','')[:600],
      'chapterIntent':next((i.get('intent','')[:600] for i in spec.get('chapterIntents',[]) if i['chapterId']==chapter_id),None),
      'overview':overview,'selectedMoments':list(map(moment,selected)),'links':links,
      'totalMoments':len(all_moments),'selectedChapterMomentCount':len(chapter),
      'referenceBindings':version.get('referenceBindings',[])[:8],'projection':'bounded editorial context; full intent/DAG remains saved',
      'retrieval':{'operation':'book.get.v1','chapterId':chapter_id,'page':0,'version':version['version'],'guidePath':'workflows/book-planning.md'},
      'revisionWorkflow':'Use exact selected saved version/hash and one book.patch.v1 request; do not explore whole thread. Full production requires separate chapter go.'}
