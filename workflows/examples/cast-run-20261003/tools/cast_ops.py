"""Use the active verified business bundle and prepared image registration argv."""
import json
import subprocess
import sys
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]
RUNTIME = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deployment = json.loads((RUNTIME / 'current-deployment.json').read_text())
sys.path.insert(0, str(RUNTIME / 'stable-releases' / deployment['stableRelease']))
from store import Store, atomic_json
from business_runtime import BusinessRuntime

def rank_reference_pack(references):
    """Rank/cap native image inputs using saved tool policy; retain all omissions."""
    policy=json.loads((DATA/'workflows/toolchain.json').read_text()).get('imageGeneration',{})
    limit=policy.get('maxInputReferences',5)
    if not isinstance(limit,int) or not 1 <= limit <= 5:
        raise ValueError('Native image reference limit must be between one and five')
    order=policy.get('rolePriority',['PRIMARY','identity','counterpart','layout','style','context'])
    def rank(ref):
        role=ref.get('role','').lower()
        kind=('PRIMARY' if 'primary' in role or 'edit-target' in role else 'counterpart' if 'counterpart' in role
              else 'layout' if 'layout' in role else 'style' if 'style' in role else 'identity' if 'identity' in role else 'context')
        return order.index(kind) if kind in order else len(order)
    unique={}
    for ref in sorted(references,key=rank):
        unique.setdefault(ref['assetId'],ref)
    ranked=list(unique.values())
    return ranked[:limit],ranked[limit:]

def finish_records(identifier, result):
    """Derive closeout metadata from existing real call receipts, preserving evidence."""
    path = DATA / 'reports/character-packages' / (identifier + '-generation.json')
    record = json.loads(path.read_text())
    calls = record['calls']
    recovered = record.get('recoveredCalls', [])
    parse = lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S UTC')
    record['metrics'] = {'imageCalls': len(calls) + len(recovered), 'measuredImageCalls': len(calls),
        'recoveredRendersWithoutMeasuredBounds': len(recovered), 'repairCalls': sum(bool(c.get('repair')) for c in calls + recovered),
        'summedImageCallWindowSeconds': sum((parse(c['generationAfterUTC'])-parse(c['generationBeforeUTC'])).total_seconds() for c in calls),
        'registrationSeconds': sum(c['receipt']['timing']['registrationSeconds'] for c in calls + recovered),
        'firstPassBodyDirectionErrors': calls[0].get('firstPassBodyWrongCells', []), 'endToEndSeconds': None, 'monetaryCost': None}
    record.update(finalStages=result['stages'], status='produced')
    folder = DATA / 'workflows/characters' / identifier
    atomic_json(path, record)
    atomic_json(folder / 'generation.json', record)
    ep = folder / 'evidence.json'; evidence = json.loads(ep.read_text())
    evidence.update(finalStages=result['stages'], generationRecord='generation.json')
    atomic_json(ep, evidence)
    doc = folder / 'README.md'; text = doc.read_text()
    start, end = '<!-- cast-ops metrics begin -->', '<!-- cast-ops metrics end -->'
    if start in text and end in text:
        before, tail = text.split(start, 1); text = before + tail.split(end, 1)[1]
    m = record['metrics']
    doc.write_text(text.rstrip()+f'\n\n{start}\n## Measured generation and decisions\n\n[Exact prompts, input roles, lineage and timings](generation.json). {m["imageCalls"]} retained native renders ({m["measuredImageCalls"]} with measured call windows, {len(recovered)} recovered without boundaries); {m["repairCalls"]} repairs; {m["summedImageCallWindowSeconds"]:.0f}s summed measured submitted-call windows. Registration {m["registrationSeconds"]:.6f}s separately measured. First-pass body errors: {m["firstPassBodyDirectionErrors"]}. These are not end-to-end latency or parallel-compute measurements; billing is unknown. Retained candidates, attribution limits and repair reasons remain in generation.json. Agent QA, no personal Miguel approval.\n{end}\n')
    result['metrics'] = m
    result['generationPath'] = str(path.relative_to(DATA))
    atomic_json(DATA / 'reports/character-packages' / (identifier + '-completion.json'), result)
    return result

def complete_inventory(store, run):
    """Export the reconciled complete queue, preserving source and legacy receipts."""
    state = store.read()
    assets = {a['id']: a for a in state.get('assets', [])}
    bindings = state['project']['book'].get('characterReferenceDefaults', {}).get('characters', {})
    entries = []
    lines = ['# Complete cast draft inventory', '',
        'All final stages below were reconciled against real registered assets, SHA-256 hashes and image bytes. Produced drafts and agent QA remain separate from human acceptance, story-reference selection and publication.', '',
        'Notetaker is unavailable. Character Markdown dossiers, source bibliography and retained receipts are the durable fallback. Missing historical generation, delivery or billing measurements remain unknown.', '',
        '| Character | Final solo | Final interactions | Age / life stage | Records |',
        '| --- | --- | --- | --- | --- |']
    for row in run['characters']:
        identifier = row['id']
        if not row['complete']: raise ValueError('Complete inventory requires every real stage')
        folder = DATA/'workflows/characters'/identifier
        doc = folder/'README.md'; evidence = folder/'evidence.json'
        package = DATA/'reports/character-packages'/(identifier+'.json')
        if not all(p.is_file() for p in (doc, evidence, package)): raise ValueError('Missing dossier/receipt: '+identifier)
        source = json.loads(evidence.read_text())
        receipt = json.loads(package.read_text())
        finals = {}
        for stage, verified in row['stages'].items():
            candidate = next(c for c in receipt['stages'][stage]['candidates'] if c['assetId']==verified['assetId'] and c['sha256']==verified['sha256'])
            asset = assets.get(verified['assetId'])
            if asset is None: raise ValueError('Verified asset missing from current registry: '+identifier)
            finals[stage] = dict(verified, registeredPath=str(store.asset_path(verified['assetId'])),
                provenance=asset.get('provenance', {}), candidateReceipt=candidate,
                retainedAttemptCount=len(receipt['stages'][stage]['candidates']))
        generation = folder/'generation.json'
        entry = {'id': identifier, 'canonicalName': row.get('canonicalName', identifier),
            'exactAge': row.get('exactAge', 'not stated'), 'evidencedLifeStage': row.get('evidencedLifeStage', 'See sourced dossier'),
            'status': 'produced', 'finalStages': finals,
            'dossierPath': str(doc.relative_to(DATA)), 'dossierText': doc.read_text(),
            'evidencePath': str(evidence.relative_to(DATA)), 'sourceBibliography': source.get('bibliography', []),
            'inspectedVisualEvidence': source.get('inspectedVisualEvidence', []),
            'designBasis': bindings.get(identifier, {}).get('designBasis', 'See preserved source/proposal distinctions in dossier and indexed evidence'),
            'sourceAndRoleBinding': bindings.get(identifier, {}), 'receiptPath': str(package.relative_to(DATA)),
            'stageReceipts': receipt,
            'generationPath': str(generation.relative_to(DATA)) if generation.is_file() else None,
            'generationRecord': json.loads(generation.read_text()) if generation.is_file() else None,
            'legacyTimingAndPromptReports': sorted({p for role in receipt['stages'].values() for c in role['candidates'] for p in c.get('sourceReportPaths', [])}),
            'authority': 'Agent QA / draft production only; no invented personal Miguel approval or publication'}
        entries.append(entry)
        stage_link = lambda role: '['+finals[role]['assetId']+']('+finals[role]['registeredPath']+')'
        lines.append('| '+entry['canonicalName']+' | '+stage_link('solo')+' | '+stage_link('interactions')+' | '+entry['exactAge']+'; '+entry['evidencedLifeStage'].replace('|','/')+' | [Dossier](../'+entry['dossierPath']+') · [Evidence](../'+entry['evidencePath']+') · [Receipts](../'+entry['receiptPath']+') |')
    payload = {'schemaVersion': 1, 'producedCount': len(entries), 'remaining': [], 'characters': entries,
        'notetaker': 'Unavailable; truthful durable Markdown fallback', 'timingLimits': 'Per-attempt generation and registration receipts; unknown historical, delivery and billing values remain unknown.'}
    paths = [DATA/'reports/cast-complete-inventory.json', DATA/'reports/cast-complete-inventory.md']
    atomic_json(paths[0], payload); paths[1].write_text('\n'.join(lines)+'\n')
    return paths

def checkpoint(runtime, store, batch, identifiers):
    began = time.monotonic()
    _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
    rows = {c['id']: c for c in run['characters']}
    records = []
    for identifier in identifiers:
        if not rows[identifier]['complete']:
            raise ValueError('Incomplete package: '+identifier)
        result = json.loads((DATA/'reports/character-packages'/(identifier+'-completion.json')).read_text())
        if result['stages'] != rows[identifier]['stages']:
            raise ValueError('Completion receipt differs from verified stages: '+identifier)
        records.append(result)
    windows=[]
    parse=lambda s:datetime.strptime(s,'%Y-%m-%d %H:%M:%S UTC')
    for identifier in identifiers:
        record=json.loads((DATA/'reports/character-packages'/(identifier+'-generation.json')).read_text())
        windows.extend((parse(c['generationBeforeUTC']),parse(c['generationAfterUTC'])) for c in record['calls'])
    merged=[]
    for a,b in sorted(windows):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    remaining=[c['id'] for c in run['characters'] if not c['complete']]
    result={'batch':batch,'characters':records,'remaining':remaining,'nextEntityId':run['nextEntityId'], 'producedCount':sum(c['complete'] for c in run['characters']),
        'imageCalls':sum(r['metrics']['imageCalls'] for r in records),'repairCalls':sum(r['metrics']['repairCalls'] for r in records),
        'measuredImageCalls':sum(r['metrics'].get('measuredImageCalls',r['metrics']['imageCalls']) for r in records),
        'recoveredRendersWithoutMeasuredBounds':sum(r['metrics'].get('recoveredRendersWithoutMeasuredBounds',0) for r in records),
        'sumImageWindowsSeconds':sum(r['metrics']['summedImageCallWindowSeconds'] for r in records),
        'unionSubmittedWindowsSeconds':sum((b-a).total_seconds() for a,b in merged),
        'firstToLastImageSpanSeconds':(max(b for a,b in windows)-min(a for a,b in windows)).total_seconds(),
        'limits':'Submission/return windows, not compute or full-turn latency. Billing and unobserved delivery bounds unknown.'}
    summary=DATA/'reports'/('cast-'+batch+'-summary.json')
    contract=DATA/'workflows/cast-run.md'; old=contract.read_text()
    archive=DATA/'reports'/('cast-before-'+batch+'-checkpoint.md')
    if not archive.exists():archive.write_text(old)
    retained=old[old.index('## Verified batch:'):] if '## Verified batch:' in old else ''
    new=f'# Durable cast run\n\n## Current checkpoint: {batch}\n\n{result["producedCount"]} complete draft packages; {len(remaining)} remain. Next: {run["nextEntityId"]}. Remaining in order: '+', '.join(remaining)+'.\n\n'
    new+=f'{result["imageCalls"]} retained native renders ({result["measuredImageCalls"]} measured, {result["recoveredRendersWithoutMeasuredBounds"]} recovered without call bounds); {result["repairCalls"]} repairs; summed measured image windows {result["sumImageWindowsSeconds"]:.0f}s, union {result["unionSubmittedWindowsSeconds"]:.0f}s, image span {result["firstToLastImageSpanSeconds"]:.0f}s. Limits: '+result['limits']+'\n\n'
    new+=f'Finished: '+', '.join(identifiers)+f'. Exact prompts, source/proposal distinctions, visual QA, stages and timings remain in character folders and standard receipts. Existing artwork preserved. [Batch summary](../reports/cast-{batch}-summary.json). [Prior checkpoint](../reports/cast-before-{batch}-checkpoint.md). Notetaker unavailable; durable Markdown fallback.\n\nUse `python -B tools/cast_ops.py finish <entity>` after real visual QA, then `python -B tools/cast_ops.py checkpoint <batch> <entity> ...` once per batch. Receipt IDs/hashes are read programmatically; curated evidence is retained.\n\n'+retained
    inventory_paths = complete_inventory(store, run) if not remaining else []
    if inventory_paths:
        new += '\n[Complete 21-entry final-stage inventory](../reports/cast-complete-inventory.md). [Full source, prompt, reference, attempt and timing receipt inventory](../reports/cast-complete-inventory.json).\n'
    if len(new.encode())>10000:raise ValueError('Contract exceeds bounded context limit')
    contract.write_text(new)
    defaults=DATA/'exports/cast-reference-defaults.json'
    atomic_json(defaults,store.read()['project']['book'].get('characterReferenceDefaults',{}))
    paths=[contract,DATA/'workflows/cast-run.json',DATA/'workflows/character-creation.md',DATA/'workflows/toolchain.json',Path(__file__),defaults]+inventory_paths
    for identifier in identifiers:
        folder=DATA/'workflows/characters'/identifier
        paths.extend(p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix in ('.md','.json','.txt'))
        paths.extend(DATA/'reports/character-packages'/(identifier+suffix) for suffix in ('.json','-generation.json','-completion.json'))
    paths.extend(p for p in (DATA/'reports/cast-closeout-proof.json',DATA/'reports/cast-batch05-input-attempt.json') if p.is_file())
    if inventory_paths:
        paths.extend(p for p in (DATA/'exports/workflows-README.md', DATA/'exports/test_business_routes.py',
            DATA/'exports/test_cast_closeout.py', DATA/'exports/final-cast-source-receipt.json',
            DATA/'tools/test_cast_closeout.py', DATA/'tools/register_cast_spec.py',
            DATA/'tools/verify-cast-active.py') if p.is_file())
    metadata=[{'path':str(p.relative_to(DATA)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths]
    atomic_json(DATA/'exports'/('cast-'+batch+'-checkpoint-receipt.json'),{'files':metadata,'imageBinariesIncluded':False,'approvalInvented':False})
    # One bounded readback of the prepared files; no broad engineering suite.
    for item in metadata:
        if hashlib.sha256((DATA/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Readback changed: '+item['path'])
    result['checkpointSeconds']=time.monotonic()-began
    result['checkpointObservedUTC']=datetime.now(timezone.utc).isoformat()
    atomic_json(summary,result)
    return {k:result[k] for k in ('batch','producedCount','remaining','nextEntityId','imageCalls','measuredImageCalls','recoveredRendersWithoutMeasuredBounds','repairCalls','sumImageWindowsSeconds','unionSubmittedWindowsSeconds','firstToLastImageSpanSeconds','checkpointSeconds')}

def main():
    runtime = BusinessRuntime(None, RUNTIME, watch=False, read_only=True)
    store = Store(DATA)
    command, *args = sys.argv[1:]
    if command == 'register':
        cfg = json.loads((DATA / 'workflows/toolchain.json').read_text())
        receipt = json.loads(subprocess.check_output(cfg['argvPrefix'] + args, text=True))
        _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
        print(json.dumps({'receipt': receipt, 'next': run['nextEntityId']}))
    elif command == 'reconcile':
        _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
        print(json.dumps({'next': run['nextEntityId'], 'remaining': [c['id'] for c in run['characters'] if not c.get('complete')]}))
    elif command == 'finish':
        identifier = args[0]
        if len(args) == 1:
            package = json.loads((DATA / 'reports/character-packages' / (identifier + '.json')).read_text())
            solo, interactions = [package['stages'][role]['candidates'][-1]['assetId'] for role in ('solo', 'interactions')]
        else:
            identifier, solo, interactions = args
        _, result = runtime.invoke('route', store, 'POST', '/api/cast/finish', {}, {'entityId': identifier, 'assetIds': [solo, interactions],
            'qaNote': 'Inspected native pages: identity, directions, anatomy, scale/contact. Agent QA only; no personal Miguel approval.',
            'timingPath': str(Path('reports/character-packages') / (identifier + '-generation.json'))})
        print(json.dumps(finish_records(identifier, result)))
    elif command == 'checkpoint':
        print(json.dumps(checkpoint(runtime, store, args[0], args[1:])))
    runtime.close()

if __name__ == '__main__':
    main()
