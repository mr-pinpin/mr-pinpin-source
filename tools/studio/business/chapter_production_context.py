"""Bounded selected-chapter command hint; pure metadata, no Store/provider actions."""

def chapter_production_workflow(chapter):
    if not isinstance(chapter, dict) or not chapter.get('studioDraft'):
        return None
    prefix = 'tools/studio-python tools/chapter_production_ops.py'
    return {
        'chapterId': chapter['id'],
        'workflow': 'workflows/chapter-production.md',
        'commands': {
            'schema': prefix + ' schema',
            'context': prefix + ' context ' + chapter['id'],
            'dispatch': prefix + ' dispatch <request.json>',
            'claim': prefix + ' claim <jobId> --agent codex',
            'prepareBeforeGeneration': prefix + ' prepare <jobId> --agent codex --scene <sceneId> --prompt-file <exact-prompt.txt> --references-file <actual-references.json>',
            'completeScene': prefix + ' complete <jobId> --agent codex --scene <sceneId> --image <native-output.png> --prompt-file <submitted-prompt.txt> --references-file <submitted-references.json> --tool image_gen.imagegen',
            'resumeReadOnly': prefix + ' resume <jobId>',
            'fail': prefix + ' fail <jobId> --agent codex --reason <actual-failure>'
        },
        'dispatchSchema': {
            'required': ['kind', 'chapterId', 'sceneIds', 'instruction'],
            'kind': 'illustration',
            'productionScope': 'full-production or rough-preproduction',
            'optional': ['referenceIds', 'referenceBindings', 'retryOf'],
            'referenceBinding': {'assetId': '<registered ID>', 'role': '<actual role>'}
        },
        'actualReferenceSchema': [{'assetId': '<registered ID>', 'roles': ['<actual role>']}],
        'guards': [
            'Full production needs current explicit version/spec/reference-bound go; this helper never authorizes it.',
            'Existing business checks scene alignment and verified local reference bytes.',
            'Persist exact prompts/references BEFORE generation; retain actual provenance.',
            'Completion is one existing atomic artifact mutation, not approval/selection/publication.',
            'After uncertain completion inspect resume and artifact hashes before retry; no exactly-once guarantee.',
            'Failed-job retry uses new dispatch with retryOf and fresh guards; do not auto-retry generation.'
        ],
        'mutated': False
    }
